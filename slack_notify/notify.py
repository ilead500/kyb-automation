import os
import requests
from typing import Optional, Dict, Any, List

# NEW: Add prohibited lists (from company doc)
PROHIBITED_COUNTRIES = [
    "Afghanistan", "Algeria", "Bangladesh", "Belarus", "Bhutan", 
    "Bosnia and Herzegovina", "Burma (Myanmar)", "Burundi", 
    "Central African Republic", "China", 
    "The Democratic Republic of Congo", "Croatia", "Cuba", "Ethiopia", 
    "Gaza Strip", "Guinea-Bissau", "Haiti", "Iran", "Iraq", "Kenya", 
    "Kosovo", "Lebanon", "Libya", "Macedonia (North)", "Mali", 
    "Montenegro", "Morocco", "Mozambique", "Nepal", "Nicaragua", 
    "Niger", "North Korea", "Pakistan", "Qatar", "Russian Federation", 
    "Serbia", "Slovenia", "Somalia", "South Sudan", "Sudan", "Syria", 
    "Ukraine", "Venezuela (Bolivarian Republic of)", 
    "West Bank (Palestinian Territory)", "Yemen", "Zimbabwe"
    # ... [full list from company doc]
]

PROHIBITED_INDUSTRIES = [
    "Gambling", "Marijuana/cannabis", "Guns", 
    "Arms and ammunition", "Adult entertainment", 
]

def format_kyb_message(data: Dict[str, Any]) -> str:
    verification = data.get("verification_results", {})
    business = data.get("business", {})
    checklist = data.get("checklist_result", {})

    # ===== STATUS CALCULATION =====
    country_status = (
        "❌ Prohibited" 
        if business.get("country") in PROHIBITED_COUNTRIES 
        else "✅ Allowed"
    )
    industry_status = (
        "❌ Prohibited" 
        if business.get("industry") in PROHIBITED_INDUSTRIES 
        else "✅ Allowed"
    )
    
    # ===== CORE MESSAGE =====
    message = f"""
✅ *KYB Case Review: {business.get('legal_name', business.get('name', 'N/A'))}*  
📋 *Status*: {data.get('status', 'pending')}  
🆔 *Case ID*: {data.get('id', 'N/A')}  

📍 *Location*: {country_status}  
🏭 *Industry*: {industry_status}  

🔍 *Verifications*:  
   • Business Registry: {'✅ Valid' if verification.get('business_registry') == 'clear' else '❌ Invalid'}  
   • Watchlist: {'✅ Clear' if verification.get('watchlist') == 'clear' else '❌ Match'}  
   • PEP: {'✅ Clear' if verification.get('pep') == 'clear' else '❌ Match'}  
   • Adverse Media: {'✅ Clear' if verification.get('adverse_media') == 'clear' else '❌ Match'}  
   • Proof of Address: {'✅ Valid' if data.get('proof_of_address', {}).get('status') == 'approved' else '❌ Invalid'}  
"""

    # ===== FAILURES SECTION =====
    if isinstance(checklist, dict):
        failures = checklist.get("failures", [])
        if failures:
            message += "\n⚠️ *Issues Found:*\n• " + "\n• ".join(failures)
    
    return message

def format_buttons(case_id: str) -> List[dict]:
    """Standardized button format for Slack messages"""
    return [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "kyb_approve",  # ← Must match the decorator!
                    "value": f"approve_{case_id}"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "kyb_reject",
                    "value": f"reject_{case_id}"
                }
            ]
        }
    ]

def send_slack_message(data: Optional[Dict[str, Any]] = None, 
                      text: Optional[str] = None, 
                      blocks: Optional[List[dict]] = None) -> bool:
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
                *format_buttons(data.get('id', ''))  # Use the new button formatter
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

def send_email(to: str, subject: str, body: str) -> bool:
    """Mock email sender (replace with Gmail later)"""
    print(f"📧 Email Draft to {to}:\nSubject: {subject}\nBody:\n{body}")
    return True
