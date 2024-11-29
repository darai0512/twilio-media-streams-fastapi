from fastapi import (
    FastAPI, WebSocket, Request, WebSocketDisconnect, Depends, HTTPException, Header
)
from fastapi.responses import HTMLResponse
import json, base64, os, logging
from twilio.rest import Client
from twilio.request_validator import RequestValidator
import asyncio


logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(message)s')
logger = logging.getLogger(__name__)
app = FastAPI()

CHUNK_COUNT_THRESHOLD = 50
SILENT_STR = '/'
SILENT_THRESHOLD = 100
account_sid = os.environ["ACCOUNT_SID"]
auth_token = os.environ["AUTH_TOKEN"]
client = Client(account_sid, auth_token)
validator = RequestValidator(auth_token)
operators = os.environ.get("OPERATORS", "").split(',')
db = {
    'CallSid': {},   # $callSid: {'toCallSid': $callSid, 'toStreamSid': $streamSid, 'send': websocket.send_text}
    'StreamSid': {}, # $streamSid: $callSid
}

# https://www.twilio.com/docs/voice/twiml/stream SDKで動的に生成することも可能
twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://{os.getenv('DOMAIN')}/" statusCallback="https://{os.getenv('DOMAIN')}/status"></Stream>
  </Connect>
</Response>"""

async def verify_token(request: Request):
    logger.info(f"{request.method} {request.url.path} {request.headers} Body={await request.body()}")
    async with request.form() as form:
        data = {k: v for k, v in form.items()}
    if not validator.validate(f"https://{os.getenv('DOMAIN')}{request.url.path}", data, request.headers['x-twilio-signature']):
        raise HTTPException(status_code=400, detail="x-twilio-signature header invalid")

async def call_operator(request: Request):
    async with request.form() as form:
        data = {k: v for k, v in form.items()}
    print('call_operator', data.get('StreamEvent', ''))
    if data.get('StreamEvent', '') != 'stream-started':
        return
    if db['CallSid'].get(data['CallSid'], None) is None:
        # todo この処理はやりたいことを実現できておらず、非同期で応答無しなら次の担当者に掛け直す処理を実装する
        for to in operators:
            call = client.calls.create(
                url=f"https://{os.getenv('DOMAIN')}/twiml",
                to=to,
                from_=os.getenv('FROM_NUMBER'),
            )
            if call and call.sid:
                db['CallSid'][data['CallSid']] = {'toCallSid': call.sid}
                db['CallSid'][call.sid] = {'toCallSid': data['CallSid']}
                break

# todo twimlBinなどに登録が最もレイテンシの無駄がない
@app.post("/twiml", response_class=HTMLResponse,
    dependencies=[Depends(verify_token)]
)
async def twiml_endpoint():
    return twiml

# https://www.twilio.com/docs/voice/twiml/stream#statuscallback
@app.post("/status",
    dependencies=[Depends(verify_token)]
)
async def status_endpoint(request: Request):
    asyncio.create_task(call_operator(request))
    return {}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket, x_twilio_signature: str = Header(default='')):
    if not validator.validate(f"wss://{os.getenv('DOMAIN')}/", {}, x_twilio_signature): # or websocket.headers
        return await websocket.close(reason='invalid signature')
    # https://www.twilio.com/docs/voice/media-streams
    # https://www.twilio.com/docs/voice/media-streams/websocket-messages
    await websocket.accept()
    payloads = []
    chunk_num = 1
    last_ts = 0
    try:
        while True:
            chunk = await websocket.receive_text()
            try:
                data = json.loads(chunk)
                logger.info(chunk)
            except:
                break
            if data['event'] == 'connected' or \
               data['event'] == 'mark' or \
               data['event'] == 'dtmf':
                continue
            elif data['event'] == 'start':
                call_sid = data['start']['callSid']
                db['StreamSid'][data['streamSid']] = call_sid
                to_call_sid = db['CallSid'][call_sid]['toCallSid']
                db['CallSid'][to_call_sid]['toStreamSid'] = data['streamSid']
                db['CallSid'][to_call_sid]['send'] = websocket.send_text
                continue
            elif data['event'] == 'media':
                stream_sid = data['streamSid']
                call_sid = db['StreamSid'].get(stream_sid, None)
                if call_sid is None:
                    logger.info("Invalid chunk order")
                    break
                media = data.get('media', None)
                if media is None or str(chunk_num) != media.get('chunk', None):
                    logger.info("Invalid chunk received")
                    continue
                chunk_num += 1
                timestamp = int(media.get('timestamp', '0'))
                payload = media.get('payload', '')
                # todo queueなどがbetter cf. https://github.com/twilio/media-streams/blob/master/python/realtime-transcriptions/SpeechClientBridge.py#L36-L56
                payloads.append(base64.b64decode(payload))

                to_stream_sid = db['CallSid'][call_sid].get('toStreamSid', None)
                if to_stream_sid is None or not await is_threshold(payloads, timestamp, last_ts, payload):
                    continue

                res = await something(payloads)
                message = {
                    'event': "media",
                    'streamSid': to_stream_sid,
                    'media': {
                         'payload': base64.b64encode(res).decode('UTF-8'),
                     },
                }
                res_json = json.dumps(message)
                await db['CallSid'][call_sid]['send'](res_json)

                # todo 必要ならmark
                # message = {
                #     'event': 'mark',
                #     'streamSid': stream_sid,
                #      'mark': {
                #          'name': f'{timestamp}',
                #      },
                # }
                payloads = []
                last_ts = timestamp
            elif data['event'] == 'stop':
                await websocket.close()
                break
            else:
                logger.info("Unknown event received: ", chunk)
                continue
    except WebSocketDisconnect:
        logger.info("Connection closed")
    except Exception as e:
        print(e)
        await websocket.close()

# todo 必要に応じて修正. 最後の引数は横着なので不要
async def is_threshold(payloads: list[bytes], timestamp: int, last_ts: int, last_payload: str) -> bool:
    return len(payloads) > CHUNK_COUNT_THRESHOLD or last_payload.count(SILENT_STR) > SILENT_THRESHOLD

# todo 必要に応じて修正. 無加工で相手に送信
async def something(payloads: list[bytes]) -> bytes:
    # audio: audio/x-mulaw with a sample rate of 8000 & chunnel=1
    audio = b"".join(payloads)
    return audio
