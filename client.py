import websocket
import json
ws = websocket.WebSocket()
ws.connect("ws://localhost:8080/")
res = {"event":"connected","protocol":"Call","version":"1.0.0"}
ws.send(json.dumps(res))
res = {"event":"start","sequenceNumber":"1","start":{"accountSid":"xxx","streamSid":"yyy","callSid":"zzz","tracks":["inbound"],"mediaFormat":{"encoding":"audio/x-mulaw","sampleRate":8000,"channels":1},"customParameters":{}},"streamSid":"yyy"}
ws.send(json.dumps(res))
res = {"event":"media","sequenceNumber":"2","media":{"track":"inbound","chunk":"1","timestamp":"171","payload":"XFVUWG3p3tnc29jSz9LfcVxYZd/NxsbM1dvPxL28xmdBNzhCYs7DwsnU7V1NQTw6PEhp0svOe01EQklUaWleVU9WXv/d0cvIyM7fXk9OX9i/sqyprLdvMyknLkq/r6ywv+5FOjMxMjZG+sO9v9hQRURRd972VEU9QEpr2svFw8DGzfhOQ0RP5sS8u77Hz9PIvLa1vn49MS85Us2+vsnlXA=="},"streamSid":"yyy"}
ws.send(json.dumps(res))
res = {"event":"mark","sequenceNumber":"3","streamSid":"yyy","mark":{"name":"171"}}
ws.send(json.dumps(res))
res = {"event":"stop","sequenceNumber":"4","streamSid":"yyy","stop":{"accountSid":"xxx","callSid":"zzz"}}
ws.send(json.dumps(res))
