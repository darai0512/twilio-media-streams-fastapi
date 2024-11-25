from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import base64
import os


HTTP_SERVER_PORT = 8080
app = FastAPI()

"""
https://www.twilio.com/docs/voice/twiml/stream
以下はSDKで動的に生成することも可能
from twilio.twiml.voice_response import Parameter, VoiceResponse, Start, Stream
"""
twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://{os.getenv('DOMAIN')}/" statusCallback="https://{os.getenv('DOMAIN')}/status"></Stream>
  </Connect>
</Response>"""
print(twiml)

def log(msg, *args):
    print(msg, *args)

@app.post("/twiml", response_class=HTMLResponse)
async def twiml_endpoint(request: Request):
    log(f"POST /twiml by {request.headers} & Body={await request.body()}")
    return twiml

@app.post("/status")
async def status_endpoint(request: Request):
    # https://www.twilio.com/docs/voice/twiml/stream#statuscallback
    log(f"POST /status by {request.headers} & Body={await request.body()}")
    return {}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    # https://www.twilio.com/docs/voice/media-streams
    # https://www.twilio.com/docs/voice/media-streams/websocket-messages
    await websocket.accept()
    payloads = []
    stream_sid = None
    chunk_num = 1
    last_ts = 0
    try:
        while True:
            chunk = await websocket.receive_text()
            try:
                data = json.loads(chunk)
                log(chunk)
            except:
                break
            if data['event'] == 'connected':
                continue
            elif data['event'] == 'start':
                stream_sid = data.get('streamSid', None)
                continue
            elif data['event'] == 'media':
                if stream_sid is None or stream_sid != data.get('streamSid', None):
                    log("Invalid chunk order")
                    continue
                media = data.get('media', None)
                if media is None or str(chunk_num) != media.get('chunk', None):
                    log("Invalid chunk received")
                    continue
                chunk_num += 1
                timestamp = int(media.get('timestamp', '0'))
                payload = media.get('payload', '')
                # todo queueなどがbetter cf. https://github.com/twilio/media-streams/blob/master/python/realtime-transcriptions/SpeechClientBridge.py#L36-L56
                payloads.append(base64.b64decode(payload))

                if not await is_threshold(payloads, timestamp, last_ts, payload):
                    continue

                res = await something(payloads)
                message = {
                    'event': "media",
                    'streamSid': stream_sid,
                    'media': {
                         'payload': base64.b64encode(res).decode('UTF-8'),
                     },
                }
                res_json = json.dumps(message)
                await websocket.send_text(res_json)

                message = {
                    'event': 'mark',
                    'streamSid': stream_sid,
                     'mark': {
                         'name': f'{timestamp}',
                     },
                }
                res_json = json.dumps(message)
                await websocket.send_text(res_json)

                payloads = []
                last_ts = timestamp
            elif data['event'] == 'mark':
                continue
            elif data['event'] == 'stop':
                break
            else:
                log("Unknown event received: ", chunk)
                continue
    except WebSocketDisconnect:
        log("Connection closed")
    except Exception as e:
        log(e)

CHUNK_COUNT_THRESHOLD = 50
SILENT_STR = '/'
SILENT_THRESHOLD = 100

# todo 必要に応じて修正. 最後の引数は横着なので不要
async def is_threshold(payloads: list[bytes], timestamp: int, last_ts: int, last_payload: str) -> bool:
    return len(payloads) > CHUNK_COUNT_THRESHOLD or last_payload.count(SILENT_STR) > SILENT_THRESHOLD

# todo 必要に応じて修正. このデモはやまびこ
async def something(payloads: list[bytes]) -> bytes:
    # audio: audio/x-mulaw with a sample rate of 8000 & chunnel=1
    audio = b"".join(payloads)
    return audio
