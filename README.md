# Media streams Demo

https://www.twilio.com/docs/voice/media-streams

# Setup & Run the server

```
$ python -m venv venv
$ source env/bin/activate
$ pip install -r requirements.txt

# or uv
$ uv venv --python 3.12
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

$source .env && curl -X POST \
  -u ${API_KEY_SID}:${API_KEY_SECRET} \
  "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Calls.json" \
  -d "To=$TO_NUMBER" -d "From=$FROM_NUMBER" -d "Url=https://$DOMAIN/twiml"
```