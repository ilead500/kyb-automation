import os
import requests

def send_slack_message(data=None, text=None, blocks=None):
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        raise Exception("SLACK_WEBHOOK_URL not set in environment variables")

    if data:
        # Fix field names to match what main.py sends
        message = {
            "text": f"📋 *KYB Case Review - {data.get('id', 'N/A')}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Business:* {data['business']['name']}\n*Status:* `{data['status']}`"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Case ID: `{data.get('id', 'N/A')}`"}
                    ]
                },
                # Add action buttons
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approve"
                            },
                            "style": "primary",
                            "value": f"approve_{data.get('id', '')}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reject"
                            },
                            "style": "danger",
                            "value": f"reject_{data.get('id', '')}"
                        }
                    ]
                }
            ]
        }
        
        # Add checklist results if available
        if isinstance(data.get("checklist_result"), dict):
            failures = data["checklist_result"].get("failures", [])
            if failures:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Issues Found:*\n• " + "\n• ".join(failures)
                    }
                })
        
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()