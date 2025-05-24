import json
import os
from dotenv import load_dotenv
from slack_notify.client import SlackClient
from utils.formatter import format_payload_summary

# Load .env variables
load_dotenv()

# Load redacted KYB payload from file (optional: hardcoded JSON also works)
with open("payload_sample.json", "r") as f:
    payload = json.load(f)

# Format summary
summary_text, summary_blocks = format_payload_summary(payload)

# Send to Slack
slack_token = os.getenv("SLACK_BOT_TOKEN")
channel = os.getenv("SLACK_CHANNEL")

slack_client = SlackClient(slack_token)
slack_client.send_message(channel, summary_text, summary_blocks)
