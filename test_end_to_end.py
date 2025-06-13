import os
import requests
from slack_notify.notify import send_slack_message

def test_webhook():
    response = requests.post(
        f"{os.getenv('RAILWAY_URL')}/persona/webhook",
        json={
            "event_type": "case.created",
            "payload": {
                "id": "WEBHOOK_TEST_123",
                "business": {"name": "Webhook Test Inc"},
                "status": "pending"
            }
        },
        headers={"Persona-Signature": os.getenv("PERSONA_WEBHOOK_SECRET")}
    )
    print(f"Webhook test: {'✅' if response.ok else '❌'} {response.status_code}")

def test_slack_interaction():
    response = requests.post(
        f"{os.getenv('RAILWAY_URL')}/slack/commands",
        headers={"Authorization": f"Bearer {os.getenv('SLACK_API_TOKEN')}"},
        data={"command": "/kyb", "text": "AUTO_TEST_123"}
    )
    print(f"Slack command test: {'✅' if response.ok else '❌'} {response.status_code}")

if __name__ == "__main__":
    test_webhook()
    test_slack_interaction()