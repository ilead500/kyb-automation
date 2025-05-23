from slack_notify.notify import send_slack_message

# Simulated KYB case data for testing
test_data = {
    "case_id": "TEST-CASE-001",
    "business_name": "Test Business Inc.",
    "status": "APPROVED ✅",
    "checklist": ["All documents verified", "UBO match confirmed"],
    "notes": ["No adverse media found", "Address validated via utility bill"]
}

send_slack_message(test_data)
python test_slack.py

