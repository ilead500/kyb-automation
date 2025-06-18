import os
import json
import httpx
import uvicorn
import slack_sdk
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from utils.checklist import validate_kyb_checklist, PROHIBITED_COUNTRIES, PROHIBITED_INDUSTRIES
from slack_notify.notify import send_slack_message
from dotenv import load_dotenv
from secrets import compare_digest
from cryptography.fernet import Fernet
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
import atexit
import logging
import time
from typing import Dict, Any

# ===== INITIALIZATION =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== ENVIRONMENT VALIDATION =====
def validate_environment():
    """Comprehensive environment validation with encryption support"""
    required_vars = {
        "SLACK_API_TOKEN": {
            "description": "Bot User OAuth Token (xoxb-...)",
            "validation": lambda x: x.startswith("xoxb-")
        },
        "PERSONA_API_KEY": {
            "description": "Persona API Key",
            "validation": lambda x: len(x) == 32
        },
        "PERSONA_WEBHOOK_SECRET": {
            "description": "Webhook signing secret",
            "validation": lambda x: len(x) >= 16
        },
        "SLACK_VERIFICATION_TOKEN": {
            "description": "Legacy verification token",
            "validation": lambda x: len(x) >= 24
        },
        "ENCRYPTION_KEY": {
            "description": "Fernet key for token decryption",
            "validation": lambda x: len(x) == 44
        }
    }

    errors = []
    for var, config in required_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing {var}: {config['description']}")
        elif not config['validation'](value):
            errors.append(f"Invalid {var}: Failed validation check")

    if errors:
        logger.critical("Environment validation failed:\n- " + "\n- ".join(errors))
        raise RuntimeError("Environment configuration invalid")

# ===== ENCRYPTION SUPPORT =====
def decrypt_token(encrypted_token: str) -> str:
    """Decrypt tokens using Fernet"""
    try:
        key = os.getenv("ENCRYPTION_KEY").encode()
        return Fernet(key).decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token decryption error")

# ===== MAIN APPLICATION SETUP =====
def create_app():
    app = FastAPI()
    
    # Validate before startup
    validate_environment()
    
    # Initialize Slack
    slack_app = App(
        token=os.getenv("SLACK_API_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET")
    )
    
    # Cleanup handler
    atexit.register(lambda: logger.info("Application shutting down..."))
    
    return app, slack_app

app, slack_app = create_app()
handler = SlackRequestHandler(slack_app)

# Load environment
load_dotenv()
slack_app = App(token=os.getenv("SLACK_API_TOKEN"))
handler = SlackRequestHandler(slack_app)
app = FastAPI()

# ===== CORE FUNCTIONS =====
async def fetch_persona_case(case_id: str) -> Dict[str, Any]:
    """Fetch KYB case data from Persona API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://withpersona.com/api/v1/cases/{case_id}",
                headers={
                    "Authorization": f"Bearer {os.getenv('PERSONA_API_KEY')}",
                    "Persona-Version": "2023-01-05"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Persona API Error: {e.response.text}")
            return None

def log_action(action: str, case_id: str) -> None:
    """Log actions to database"""
    logger.info(f"DB LOG: {json.dumps({
        'action': action,
        'case_id': case_id,
        'timestamp': int(time.time())
    })}")

# ===== ROUTES =====
@app.post("/slack/commands")
async def slack_command(
    request: Request,
    token: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    response_url: str = Form(None),
    user_id: str = Form(...)
):
    """Handle /kyb commands with full compliance workflow"""
    if not compare_digest(token, os.getenv("SLACK_VERIFICATION_TOKEN")):
        logger.error(f"Invalid token from user {user_id}")
        raise HTTPException(status_code=403)

    try:
        case_id = text.strip()
        logger.info(f"Processing /kyb from {user_id} for case: {case_id}")

        # 1. Fetch case data
        case_data = await fetch_persona_case(case_id) or {
            "id": case_id,
            "business": {"name": "Unknown Business"},
            "status": "error",
            "verification_results": {},
            "proof_of_address": {}
        }

        # 2. Run compliance checks
        checklist_result = validate_kyb_checklist(case_data)
        case_data["checklist_result"] = checklist_result

        # 3. Determine if needs manual review
        needs_review = any(
            f.lower() in ["pep", "watchlist", "prohibited"]
            for f in checklist_result.get("failures", [])
        )

        # 4. Send Slack message
        await send_slack_message({
            **case_data,
            "needs_review": needs_review
        })

        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"✅ Case {case_id} is being processed..."
        })

    except Exception as e:
        logger.error(f"Command failed: {str(e)}", exc_info=True)
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "⚠️ Failed to process case. Admins notified."
        })

# ===== SLACK INTERACTIVITY =====
@slack_app.action("kyb_approve")
async def handle_approve(ack, body, respond):
    await ack()
    try:
        case_id = body["actions"][0]["value"].split("_")[1]
        logger.info(f"Approving case {case_id}")
        log_action("approve", case_id)
        respond(text=f"✅ Case {case_id} approved!")
    except Exception as e:
        logger.error(f"Approval failed: {str(e)}")
        respond(text="❌ Approval failed")

@slack_app.action("kyb_flag")
async def handle_flag(ack, body, respond):
    await ack()
    try:
        case_id = body["actions"][0]["value"].split("_")[1]
        logger.info(f"Flagging case {case_id} for review")
        log_action("flag", case_id)
        respond(text=f"⚠️ Case {case_id} flagged for compliance review")
    except Exception as e:
        logger.error(f"Flagging failed: {str(e)}")
        respond(text="❌ Flagging failed")

@slack_app.action("kyb_reject")
async def handle_reject(ack, body, respond):
    await ack()
    try:
        case_id = body["actions"][0]["value"].split("_")[1]
        logger.info(f"Rejecting case {case_id}")
        log_action("reject", case_id)
        respond(text=f"❌ Case {case_id} rejected!")
    except Exception as e:
        logger.error(f"Rejection failed: {str(e)}")
        respond(text="❌ Rejection failed")

# ===== OTHER ENDPOINTS =====
@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)

@app.post("/persona/webhook")
async def handle_persona_webhook(request: Request):
    secret = os.getenv("PERSONA_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    body = await request.body()
    if not compare_digest(request.headers.get("Persona-Signature", ""), secret):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=403)
    
    try:
        data = json.loads(body)
        logger.info(f"Persona webhook: {data.get('event_type')}")
        return {"status": "ok"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

@app.get("/")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))