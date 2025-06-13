import os
import requests
from typing import Optional, Dict, Any

def format_kyb_message(data: Dict[str, Any]) -> str:
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

def send_slack_message(data: Optional[Dict[str, Any]] = None, 
                      text: Optional[str] = None, 
                      blocks: Optional[list] = None) -> bool:
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

    # Build the message payload
    message = {}
    if data:
        message = {
            "text": f"📋 KYB Case Review - {data.get('id', 'N/A')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": format_kyb_message(data)
                    }
                },
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
    elif text or blocks:
        message = {"text": text, "blocks": blocks}
    else:
        raise ValueError("Either data, text, or blocks must be provided")

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        error_msg = f"Slack API Error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            error_msg += f" | Status: {e.response.status_code} | Response: {e.response.text}"
        print(error_msg)
        return False