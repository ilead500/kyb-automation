from dotenv import load_dotenv
load_dotenv()
# slack_notify/notify.py
import os
import requests

def send_slack_message(data=None, text=None, blocks=None):
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        raise Exception("SLACK_WEBHOOK_URL not set in environment variables")

    # If using structured data (your original version)
    if data:
        message = {
            "text": f"📋 *KYB Case Review - {data['case_id']}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Business:* {data['business_name']}\n*Status:* `{data['status']}`"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Case ID: `{data['case_id']}`"}
                    ]
                },
            ]
        }

        # Checklist
        if data.get("checklist"):
            checklist_text = "\n".join(f"• {item}" for item in data["checklist"])
            message["blocks"].append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Checklist flags:*\n{checklist_text}"}
            })

        # Notes
        if data.get("notes"):
            notes_text = "\n".join(f"- {note}" for note in data["notes"])
            message["blocks"].append({
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"_Notes:_ {notes_text}"}]
            })

    # If using text and blocks directly (as in webhook_server.py)
    elif text or blocks:
        message = {"text": text or "KYB Notification"}
        if blocks:
            message["blocks"] = blocks

    else:
        raise ValueError("No valid data or message format provided for Slack message.")

    # Send the message
    response = requests.post(SLACK_WEBHOOK_URL, json=message)
    if response.status_code != 200:
        raise Exception(f"Slack API error: {response.text}")
