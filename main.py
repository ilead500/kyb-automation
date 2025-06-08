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

print("Current environment:", os.environ)
      
# Load environment first
load_dotenv()

# Validate critical environment variablescd
SLACK_TOKEN = os.getenv("SLACK_API_TOKEN")
PERSONA_KEY = os.getenv("PERSONA_API_KEY")
WEBHOOK_SECRET = os.getenv("PERSONA_WEBHOOK_SECRET")

required_vars = {
    "SLACK_API_TOKEN": SLACK_TOKEN,
    "PERSONA_API_KEY": PERSONA_KEY,
    "PERSONA_WEBHOOK_SECRET": WEBHOOK_SECRET
}

if not all(required_vars.values()):
    missing = [name for name, val in required_vars.items() if not val]
    raise RuntimeError(f"CRITICAL: Missing env vars - {', '.join(missing)}")

app = FastAPI()

# ===== MODELS =====
class SlackChallenge(BaseModel):
    challenge: str
    type: str

# ===== CORE FUNCTIONS =====
async def fetch_persona_case(case_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://withpersona.com/api/v1/cases/{case_id}",
                headers={
                    "Authorization": f"Bearer {os.getenv('PERSONA_API_KEY')}",
                    "Persona-Version": "2023-01-05",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Persona API Error: {e.response.text}")
            return None

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
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    # Add this verification FIRST
    body = await request.body()
    received_sig = request.headers.get("Persona-Signature", "")
    
    if not compare_digest(received_sig, WEBHOOK_SECRET):
        print(f"Invalid signature! Received: {received_sig}")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    return {"status": "ok"}

@app.post("/mock/persona-webhook")
async def mock_webhook_handler():
    """Simplified mock that directly calls the webhook logic"""
    print("EXPECTED SIGNATURE:", WEBHOOK_SECRET)
    print("Expected Secret:", WEBHOOK_SECRET)
    print("Hardcoded Test Sig:", "demo_signature")
    
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
    port = int(os.getenv("PORT", 8000))  # Railway uses PORT env var
    print("✅ KYB Automation Project Started")
    uvicorn.run(app, host="0.0.0.0", port=port)