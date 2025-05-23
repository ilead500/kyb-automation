from slack_notify.notify import send_slack_message

message_text = "Test KYB Message"
blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": "*Test Message from Python script*"}}
]

send_slack_message(text=message_text, blocks=blocks)
