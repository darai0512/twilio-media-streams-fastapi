# Twilio media-streams Demo

[Official python demo (unidirectional)](https://github.com/twilio/media-streams) is too old.

This is fastapi & bidirectional version.

ref. official docs: https://www.twilio.com/docs/voice/media-streams

# Setup & Run the server

```
$ python -m venv venv
$ source env/bin/activate
$ pip install -r requirements.txt

# or uv
$ uv venv --python 3.9
$ source .venv/bin/activate
$ uv pip install -r requirements.txt

# if you don't have public DOMAIN, run ngrok
# https://dashboard.ngrok.com/signup & https://dashboard.ngrok.com/get-started/your-authtoken
$ ngrok config add-authtoken TOKEN
$ ngrok http http://localhost:8080

# set env
$ cat .env
export ACCOUNT_SID=
export AUTH_TOKEN=
export TO_NUMBER=+YOUR_VERIFIED_PHONE
export FROM_NUMBER=+TWILIO_NUMBER
export DOMAIN=xxx.ngrok-free.app
# US
export API_KEY_SID=
export API_KEY_SECRET=

# run the server
$ source .env && uv run uvicorn main:app --reload --port 8080

# Call to your phone. Get echo of your voice
$source .env && curl -X POST \
  -u ${API_KEY_SID}:${API_KEY_SECRET} \
  "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Calls.json" \
  -d "To=$TO_NUMBER" -d "From=$FROM_NUMBER" -d "Url=https://$DOMAIN/twiml"
```

# Memo
## Vender lock-in?

Check Vonage: https://www.vonagebusiness.jp/communications-apis/phone-numbers/

## official demo requirements

https://github.com/twilio/media-streams/tree/master/python/basic is too old, so `requements.txt` is invalid.

update `requirements.txt`
```
Flask==2.0.3
Flask-Sockets==0.2.1
Werkzeug==2.0.3
```
