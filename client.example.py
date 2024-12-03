import os, json
import websocket, httpx
from twilio.request_validator import RequestValidator

account_sid = os.environ["ACCOUNT_SID"]
auth_token = os.environ["AUTH_TOKEN"]
validator = RequestValidator(auth_token)

stream_sid = 'stream_sid'
call_sid = 'call_sid'
# 1st: twiml by application/x-www-form-urlencoded
data = {
    'To': '+817011111111',
    'From': '+1000000',
    'Called': '+817011111111',
    'Caller': '+1000000',
    'FromCity': '',
    'CalledState': '',
    'FromZip': '',
    'FromState': 'CA',
    'CallerCountry': 'US',
    'ToCountry': 'JP',
    'FromCountry': 'US',
    'CalledCountry': 'JP',
    'ToState': '',
    'ToZip': '',
    'CallerZip': '',
    'CalledZip': '',
    'CalledCity': '',
    'CallerCity': '',
    'ToCity': '',
    'CallSid': call_sid,
    'CallStatus': 'in-progress',
    'Direction': 'outbound-api',
    'AccountSid': os.getenv('ACCOUNT_SID'),
    'CallerState': 'CA',
    'ApiVersion': '2010-04-01',
}
url = f"https://{os.getenv('DOMAIN')}/twiml"
signature = validator.compute_signature(url, data)
r = httpx.post(url, data=data, headers={'X-Twilio-Signature': signature})

# 2nd: websocket
url = f"wss://{os.getenv('DOMAIN')}/"
signature = validator.compute_signature(url, {})
ws = websocket.WebSocket()
ws.connect(url, header=[f'X-Twilio-Signature: {signature}'])

# 3rd: status callback
data = {
    'StreamName': stream_sid,
    'StreamEvent': 'stream-started',
    'CallSid': 'sid',
    'Timestamp': '2024-11-29T00:09:39.602648368Z',
    'AccountSid': os.getenv('ACCOUNT_SID'),
    'StreamSid': stream_sid,
}
url = f"https://{os.getenv('DOMAIN')}/status"
signature = validator.compute_signature(url, data)
r = httpx.post(url, data=data, headers={'X-Twilio-Signature': signature})

res = {"event":"connected","protocol":"Call","version":"1.0.0"}
ws.send(json.dumps(res))
res = {"event":"start","sequenceNumber":"1","start":{"accountSid":account_sid,"streamSid":stream_sid,"callSid":call_sid,"tracks":["inbound"],"mediaFormat":{"encoding":"audio/x-mulaw","sampleRate":8000,"channels":1},"customParameters":{}},"streamSid":stream_sid}
ws.send(json.dumps(res))
res = {"event":"media","sequenceNumber":"2","media":{"track":"inbound","chunk":"1","timestamp":"171","payload":"XFVUWG3p3tnc29jSz9LfcVxYZd/NxsbM1dvPxL28xmdBNzhCYs7DwsnU7V1NQTw6PEhp0svOe01EQklUaWleVU9WXv/d0cvIyM7fXk9OX9i/sqyprLdvMyknLkq/r6ywv+5FOjMxMjZG+sO9v9hQRURRd972VEU9QEpr2svFw8DGzfhOQ0RP5sS8u77Hz9PIvLa1vn49MS85Us2+vsnlXA=="},"streamSid":stream_sid}
ws.send(json.dumps(res))
res = {"event":"mark","sequenceNumber":"3","streamSid":stream_sid,"mark":{"name":"171"}}
ws.send(json.dumps(res))
res = {"event":"stop","sequenceNumber":"4","streamSid":stream_sid,"stop":{"accountSid":account_sid,"callSid":call_sid}}
ws.send(json.dumps(res))

# end: status callback
data = {
    'StreamName': stream_sid,
    'StreamEvent': 'stream-stopped',
    'CallSid': 'sid',
    'Timestamp': '2024-11-29T00:09:39.602648368Z',
    'AccountSid': os.getenv('ACCOUNT_SID'),
    'StreamSid': stream_sid,
}
url = f"https://{os.getenv('DOMAIN')}/status"
signature = validator.compute_signature(url, data)
r = httpx.post(url, data=data, headers={'X-Twilio-Signature': signature})
