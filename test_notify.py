# Create test_notify.py
from slack_notify.notify import send_slack_message

test_data = {
    "business": {"name": "Test Corp"},
    "status": "pending",
    "id": "TEST123",
    "checklist_result": {"failures": []}
}

result = send_slack_message(data=test_data)
print("Success!" if result else "Failed")