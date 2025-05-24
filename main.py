from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from utils.checklist import validate_kyb_checklist
from slack.notify import send_slack_message

app = FastAPI()

@app.post("/slack/commands")
async def slack_command(request: Request):
    form = await request.form()
    case_id = form.get("text")  # Expected format: case ID passed from slash command

    # In real scenario, you'd fetch KYB data using the case_id.
    # For now, let's simulate it with test data:
    fake_payload = {
        "kyb_case_id": case_id,
        "business": {"name": "Test Business"},
        "control_person": {"name": "John Doe"},
        "beneficial_owners": [{"name": "Jane Smith"}],
        "verification": {"status": "verified"},
        "documents": [{"type": "passport", "verified": True}]
    }

    checklist_result = validate_kyb_checklist(fake_payload)

    business_name = fake_payload["business"]["name"]
    message_text = f"*KYB Review for*: `{business_name}`\n*Case ID:* `{case_id}`"

    if checklist_result["passed"]:
        status = ":white_check_mark: *AUTO-APPROVED*"
        note = "All checks passed ✅"
    else:
        status = ":warning: *REVIEW REQUIRED*"
        note = "\n".join(f"- {f}" for f in checklist_result["failures"])

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{status}\n\n{message_text}"}} ,
        {"type": "context", "elements": [{"type": "mrkdwn", "text": note}]},
        {"type": "actions", "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Open in Persona"},
                "url": f"https://withpersona.com/cases/{case_id}",
                "style": "primary"
            }
        ]}
    ]

    send_slack_message(text=message_text, blocks=blocks)

    return JSONResponse({"response_type": "ephemeral", "text": "Processing your request..."})

# Entry point
if __name__ == "__main__":
    print("✅ KYB Automation Project Started")
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
    import uvicorn

@app.get("/")
async def root():
    return {"message": "✅ KYB Automation API is live"}





