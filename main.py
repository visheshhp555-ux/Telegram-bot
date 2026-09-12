import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.getenv("BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

offset = 0

print("🤖 Bot started...")

def telegram(method, data=None):
    if data is None:
        data = {}

    data = urllib.parse.urlencode(data).encode()

    request = urllib.request.Request(
        f"{API}/{method}",
        data=data
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


while True:
    try:
        result = telegram(
            "getUpdates",
            {
                "offset": offset,
                "timeout": 30
            }
        )

        for update in result.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            text = message.get("text", "")
            chat_id = message["chat"]["id"]

            if text.lower() == "/start":
                telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "🤖 Bot Online!"
                    }
                )

            elif text.lower() == "/unban":
                telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": "⚙️ /unban command received."
                    }
                )

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
