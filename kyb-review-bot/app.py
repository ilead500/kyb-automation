from flask import Flask, request, jsonify
import os
from utils.checklist import validate_kyb_checklist
from slack.notify import send_slack_message

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    checklist_result = validate_kyb_checklist(data)

    business_name = data.get("business", {}).get("name", "Unknown Business")
    case_id = data.get("kyb_case_id", "No Case ID")

    message_text = f"*KYB Review for*: `{business_name}`\n*Case ID:* `{case_id}`"

    if checklist_result["passed"]:
        status = ":white_check_mark: *AUTO-APPROVED*"
        note = "All checks passed ✅"
    else:
        status = ":warning: *REVIEW REQUIRED*"
        note = "\n".join(f"- {f}" for f in checklist_result["failures"])

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{status}\n\n{message_text}"}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"{note}"}]},
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

    return jsonify({"message": "Notification sent"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)

