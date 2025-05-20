from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

app = FastAPI()

@app.post("/slack/commands")
async def handle_slack_command(request: Request):
    form_data = await request.form()
    command = form_data.get("command")
    user_id = form_data.get("user_id")

    if command == "/check_case":
        return JSONResponse({
            "response_type": "in_channel",
            "text": f"👀 Running KYB check for you <@{user_id}>... 🔍"
        })

    return JSONResponse({"text": "Unknown command"})
def main():
    print("KYB Automation Project Started")

if __name__ == "__main__":
    main()

python app/main.py

dir
