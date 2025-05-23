# test_webhook.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

if not SLACK_WEBHOOK_URL:
    raise Exception("SLACK_WEBHOOK_URL is not set in .env file")

# Build a simple test message
message = {
    "text": "🚀 *Webhook Test Successful!*",
    "blocks": [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*This is a test message sent via webhook.*"}
        }
    ]
}

# Send to Slack
response = requests.post(SLACK_WEBHOOK_URL, json=message)

# Check response
if response.status_code == 200:
    print("✅ Message sent successfully!")
else:
    print(f"❌ Failed to send message. Error: {response.text}")
