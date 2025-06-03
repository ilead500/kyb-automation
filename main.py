# main.py (or your entry point file)
from dotenv import load_dotenv  # Note the double backslashes!
import os

# Now you can safely use os.getenv()
slack_token = os.getenv("SLACK_API_TOKEN")
persona_key = os.getenv("PERSONA_API_KEY")
import uvicorn
import os
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

@app.post("/slack/commands")
async def slack_command(request: "Request"):
 # Replace form_data with direct JSON parsing
    try:
        json_data = await request.json()
        case_id = json_data.get("text")
        
        if not case_id:
            raise HTTPException(status_code=400, detail="Missing 'text' field")
        
        case_data = await fetch_persona_case(case_id)
        checklist_result = validate_kyb_checklist(case_data)
        await send_slack_message(case_data, checklist_result)
        return JSONResponse(
            {"response_type": "ephemeral", "text": "Processing your request..."}
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    # Verify webhook secret
    if request.headers.get("Persona-Signature") != os.getenv("PERSONA_WEBHOOK_SECRET"):
        raise HTTPException(status_code=403)

    data = await request.json()
    
    if data.get("event_type") == "case.created":
        case_id = data["payload"]["id"]
        case_data = await fetch_persona_case(case_id)
        checklist_result = validate_kyb_checklist(case_data)
        await send_slack_message(case_data, checklist_result)
    
    return {"status": "ok"}

@app.post("/mock/persona-webhook")
async def mock_persona_webhook():
    """Test endpoint that mimics Persona's real webhook payload"""
    test_payload = {
        "event_type": "case.created",
        "payload": {
            "id": "test_123",
            "business": {"name": "Test Business LLC"},
            "verification": {"status": "pending"},
            "documents": [{"type": "license", "status": "required"}]
        }
    }
    
    fake_request = Request(
        scope={
            "type": "http",
            "headers": [(b"persona-signature", b"mock_signature")]
        },
        receive=None,
        send=None,
        body=json.dumps(test_payload).encode()
    )
    
    return await handle_persona_webhook(fake_request)

# ===== ENTRY POINT =====
if __name__ == "__main__":
    print("✅ KYB Automation Project Started")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)