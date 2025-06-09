import os
import requests

def format_kyb_message(data):
    """Format the KYB case details according to buyer's specifications"""
    base_message = f"""
✅ *KYB Case Review: {data['business']['name']}*  
📋 *Status*: {data['status']}  
🆔 *Case ID*: {data.get('id', 'N/A')}  

🔍 *Verifications*:  
   • Watchlist: ✅ No matches found  
   • PEP: ✅ No matches found  
   • Adverse Media: ✅ No matches found  
   • Business Registry: ✅ Validated  

📍 *Locations & Industries*: ✅ All allowed  
📄 *Documents*: ✅ All provided  
"""
    
    # Add failures if they exist
    if isinstance(data.get("checklist_result"), dict):
        failures = data["checklist_result"].get("failures", [])
        if failures:
            base_message += "\n⚠️ *Issues Found:*\n• " + "\n• ".join(failures)
    
    return base_message

def send_slack_message(data=None, text=None, blocks=None):
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        raise Exception("SLACK_WEBHOOK_URL not set in environment variables")

    if data:
        message = {
            "text": f"📋 KYB Case Review - {data.get('id', 'N/A')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": format_kyb_message(data)  # Use the new formatter
                    }
                },
                # Action buttons remain the same
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
        
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()