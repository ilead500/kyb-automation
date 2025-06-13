import requests
import json
import hmac
import hashlib

webhook_url = "http://localhost:8000/persona/webhook"
secret = "your_test_secret"  # Match PERSONA_WEBHOOK_SECRET

payload = {
    "event_type": "case.created",
    "payload": {
        "id": "LOCAL_TEST_001",
        "business": {"name": "Local Test Inc"}
    }
}

# Generate signature
signature = hmac.new(
    secret.encode(),
    json.dumps(payload).encode(),
    hashlib.sha256
).hexdigest()

response = requests.post(
    webhook_url,
    json=payload,
    headers={"Persona-Signature": signature}
)

print(f"Status: {response.status_code}, Response: {response.text}")
