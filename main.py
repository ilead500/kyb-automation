import os
from dotenv import load_dotenv  # Note the double backslashes!
# Now you can safely use os.getenv()
slack_token = os.getenv("SLACK_API_TOKEN")
persona_key = os.getenv("PERSONA_API_KEY")
import uvicorn
import json
import httpx
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from utils.checklist import validate_kyb_checklist
from slack_notify.notify import send_slack_message
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# ===== MODELS =====
class SlackChallenge(BaseModel):
    challenge: str
    type: str

# ===== CORE FUNCTIONS =====
async def fetch_persona_case(case_id: str):
    """Fetch case details from Persona API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://withpersona.com/api/v1/cases/{case_id}",
            headers={
                "Authorization": f"Bearer {os.getenv('PERSONA_API_KEY')}",
                "Persona-Version": "2023-01-05"
            }
        )
        return response.json()

# ===== ROUTES =====
@app.get("/")
async def root():
    return {"message": "KYB Bot is running"}

# REPLACE THIS ENTIRE BLOCK ▼▼▼
@app.post("/slack/commands")
async def slack_command(request: Request):
    try:
        data = await request.json()
        case_id = data.get("text", "CASE-DEMO-001")  # Default for demo
        
        # DEMO-ONLY MOCK DATA
        mock_data = {
            "id": case_id,
            "business": {
                "name": "Demo Business LLC",
                "incorporation_country": "US"
            },
            "control_person": {
                "full_name": "Demo Owner"
            },
            "status": "pending",
            "verification": {
                "watchlist": "clear",
                "business_registry": "verified"
            }
        }
        
        checklist_result = validate_kyb_checklist(mock_data)
        await send_slack_message(mock_data, checklist_result)
        
        return JSONResponse({
            "response_type": "ephemeral", 
            "text": f"✅ Demo case {case_id} processed"
        })
        
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")  # Critical for troubleshooting
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error: {str(e)}"
        })

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    # Get the expected signature from environment
    expected_sig = os.getenv("PERSONA_WEBHOOK_SECRET")
    if not expected_sig:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    # Compare signatures securely
    received_sig = request.headers.get("Persona-Signature")
    if not received_sig or received_sig != expected_sig:
        print(f"Signature mismatch. Expected: {expected_sig}, Received: {received_sig}")
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    print(f"Webhook received: {data}")
    
    if data.get("event_type") == "case.created":
        case_id = data["payload"]["id"]
        case_data = await fetch_persona_case(case_id)
        checklist_result = validate_kyb_checklist(case_data)
        await send_slack_message(case_data, checklist_result)
    
    return {"status": "ok"}

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    # Get the expected signature from environment
    expected_sig = os.getenv("PERSONA_WEBHOOK_SECRET")
    if not expected_sig:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    # Compare signatures securely
    received_sig = request.headers.get("Persona-Signature")
    if not received_sig or received_sig != expected_sig:
        print(f"Signature mismatch. Expected: {expected_sig}, Received: {received_sig}")
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    print(f"Webhook received: {data}")
    
    if data.get("event_type") == "case.created":
        case_id = data["payload"]["id"]
        case_data = await fetch_persona_case(case_id)
        checklist_result = validate_kyb_checklist(case_data)
        await send_slack_message(case_data, checklist_result)
    
    return {"status": "ok"}

@app.post("/mock/persona-webhook")
async def mock_persona_webhook():
    try:
        test_payload = {
            "event_type": "case.created",
            "payload": {
                "id": "CASE-DEMO-001",
                "business": {
                    "name": "Demo Client Inc",
                    "incorporation_country": "US"
                },
                "control_person": {
                    "full_name": "Demo Director"
                },
                "status": "pending",
                "verification": {
                    "watchlist": "clear"
                }
            }
        }
        
        # Bypass signature check for demo
        fake_request = Request(
            scope={
                "type": "http",
                "headers": [
                    (b"persona-signature", b"demo_signature"),
                    (b"content-type", b"application/json")
                ]
            },
            receive=None,
            send=None,
            body=json.dumps(test_payload).encode()
        )
        
        # Directly call the processing logic
        data = await fake_request.json()
        case_id = data["payload"]["id"]
        checklist_result = validate_kyb_checklist(data["payload"])
        await send_slack_message(data["payload"], checklist_result)
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"WEBHOOK ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENTRY POINT =====
if __name__ == "__main__":
    print("✅ KYB Automation Project Started")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)