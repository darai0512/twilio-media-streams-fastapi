from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator
from main import app, byte_to_nparray
import os

auth_token = os.environ["AUTH_TOKEN"]
client = TestClient(app)
validator = RequestValidator(auth_token)
url = f"https://{os.getenv('DOMAIN')}"


def test_twiml():
    path = '/twiml'
    signature = validator.compute_signature(url + path, {})
    response = client.post(path, headers={'X-Twilio-Signature': signature})
    assert response.status_code == 200
    assert response.text == f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://{os.getenv('DOMAIN')}/" statusCallback="https://{os.getenv('DOMAIN')}/status"></Stream>
  </Connect>
</Response>"""

def test_byte_to_nparray():
    pass
