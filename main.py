import os
import json
import httpx
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from utils.checklist import validate_kyb_checklist
from slack_notify.notify import send_slack_message
from dotenv import load_dotenv
from secrets import compare_digest

# Load environment first
load_dotenv()

# Validate critical environment variables
SLACK_TOKEN = os.getenv("SLACK_API_TOKEN")
PERSONA_KEY = os.getenv("PERSONA_API_KEY")
WEBHOOK_SECRET = os.getenv("PERSONA_WEBHOOK_SECRET")

if not all([SLACK_TOKEN, PERSONA_KEY, WEBHOOK_SECRET]):
    raise RuntimeError("Missing required environment variables")

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
                "Authorization": f"Bearer {PERSONA_KEY}",  # Use the pre-loaded variable
                "Persona-Version": "2023-01-05"
            }
        )
        response.raise_for_status()
        return response.json()

# ===== ROUTES =====
@app.get("/")
async def root():
    return {"message": "KYB Bot is running"}

@app.post("/slack/commands")
async def slack_command(request: Request):
    try:
        # Debug raw request body
        raw_body = await request.body()
        print("Raw request body:", raw_body)
              
        try:
            data = await request.json()
        except json.JSONDecodeError:
            print("Invalid JSON received!")
            return JSONResponse(
                {"error": "Invalid JSON"}, 
                status_code=400
            )
    
        case_id = data.get("text", "CASE-DEMO-001").strip()
        
        # Create properly structured data
        case_data = {
            "id": case_id,
            "case_id": case_id,  # Duplicate for compatibility
            "business": {
                "name": "Demo Business LLC",
                "incorporation_country": "US"
            },
            "control_person": {
                "full_name": "Demo Owner"
            },
            "status": "pending",
            "verification": {
                "watchlist": "clear"
            }
        }
        
        checklist_result = validate_kyb_checklist(case_data)
        case_data["checklist_result"] = checklist_result  # Add to payload
        
        await send_slack_message(case_data)
        
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"Processed case: {case_id}"
        })
    except Exception as e:
        print(f"Slack command error: {str(e)}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    # Signature verification
    received_sig = request.headers.get("Persona-Signature")
    if not compare_digest(received_sig or "", WEBHOOK_SECRET):
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
async def mock_webhook_handler():
    """Simplified mock that directly calls the webhook logic"""
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
            "status": "pending"
        }
    }
    
    # Create a mock request
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    scope = {
        "type": "http",
        "headers": [
            (b"persona-signature", b"demo_signature"),
            (b"content-type", b"application/json")
        ]
    }
    
    mock_request = StarletteRequest(scope=scope)
    mock_request._body = json.dumps(test_payload).encode()
    
    return await handle_persona_webhook(mock_request)

@app.get("/slack/oauth_callback")
async def slack_oauth_callback(code: str):
    # Exchange the code for a token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "code": code,
                "client_id": os.getenv("SLACK_CLIENT_ID"),
                "client_secret": os.getenv("SLACK_CLIENT_SECRET")
            }
        )
        return response.json()  # Returns access tokens

if __name__ == "__main__":
    print("✅ KYB Automation Project Started")
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Consistent port