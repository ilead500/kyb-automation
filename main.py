import os
import json
import httpx
import uvicorn
import slack_sdk
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from utils.checklist import validate_kyb_checklist
from slack_notify.notify import send_slack_message
from dotenv import load_dotenv
from secrets import compare_digest
from cryptography.fernet import Fernet
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
import atexit
import logging
import time

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Slack Bolt
slack_app = App(token=os.getenv("SLACK_API_TOKEN"))
handler = SlackRequestHandler(slack_app)

# Cleanup handler
atexit.register(lambda: logger.info("Shutting down..."))

def decrypt_token(encrypted_token: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    return Fernet(key).decrypt(encrypted_token.encode()).decode()

print("Current environment:", os.environ)
load_dotenv()

# Validate environment variables
required_vars = {
    "SLACK_API_TOKEN": os.getenv("SLACK_API_TOKEN"),
    "PERSONA_API_KEY": os.getenv("PERSONA_API_KEY"),
    "PERSONA_WEBHOOK_SECRET": os.getenv("PERSONA_WEBHOOK_SECRET"),
    "SLACK_VERIFICATION_TOKEN": os.getenv("SLACK_VERIFICATION_TOKEN")
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
            logger.error(f"Persona API Error: {e.response.text}")
            return None

def log_to_db(action_data: dict):
    """Simple DB logger (replace with actual implementation)"""
    logger.info(f"DB LOG: {json.dumps(action_data)}")
    return True

# ===== ROUTES =====
@app.get("/")
async def root():
    return {"message": "KYB Bot is running"}

@app.post("/slack/commands")
async def slack_command(
    token: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    response_url: str = Form(None)
):
    if not compare_digest(token, os.getenv("SLACK_VERIFICATION_TOKEN")):
        raise HTTPException(status_code=403)
    
    try:
        case_id = text.strip()
        logger.info(f"Processing /kyb command for case: {case_id}")

        # Replace with actual Persona data fetching
        case_data = {
            "id": case_id,
            "business": {"name": "Demo Business LLC"},
            "status": "pending",
            "verification": {"watchlist": "clear"}
        }
        
        checklist_result = validate_kyb_checklist(case_data)
        case_data["checklist_result"] = checklist_result
        
        await send_slack_message(case_data)
        
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"✅ Case {case_id} is being processed..."
        })
    except Exception as e:
        logger.error(f"Slack command failed: {str(e)}")
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "⚠️ Failed to process case. Admin notified."
        })

@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)

@slack_app.action("kyb_approve")
async def handle_approve(ack, body, respond):
    await ack()
    try:
        case_id = body["actions"][0]["value"].split("_")[1]
        logger.info(f"Approving case {case_id}")
        log_to_db({
            "action": "approve",
            "case_id": case_id,
            "timestamp": int(time.time())
        })
        respond(text=f"✅ Case {case_id} approved!")
    except Exception as e:
        logger.error(f"Approval failed: {str(e)}")
        respond(text="❌ Approval failed")

@slack_app.action("kyb_reject")
async def handle_reject(ack, body, respond):
    await ack()
    try:
        case_id = body["actions"][0]["value"].split("_")[1]
        logger.info(f"Rejecting case {case_id}")
        log_to_db({
            "action": "reject",
            "case_id": case_id,
            "timestamp": int(time.time())
        })
        respond(text=f"❌ Case {case_id} rejected!")
    except Exception as e:
        logger.error(f"Rejection failed: {str(e)}")
        respond(text="❌ Rejection failed")

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    if not os.getenv("PERSONA_WEBHOOK_SECRET"):
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    body = await request.body()
    received_sig = request.headers.get("Persona-Signature", "")
    
    if not compare_digest(received_sig, os.getenv("PERSONA_WEBHOOK_SECRET")):
        logger.error(f"Invalid webhook signature: {received_sig}")
        raise HTTPException(status_code=403)
    
    try:
        data = json.loads(body)
        logger.info(f"Received Persona webhook: {data.get('event_type')}")
        return {"status": "ok"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info("✅ KYB Automation Project Started")
    uvicorn.run(app, host="0.0.0.0", port=port)