import requests
import time

TOKEN = "YOUR_BOT_TOKEN"
API = f"https://api.telegram.org/bot{TOKEN}"

offset = 0

print("🤖 Bot started...")

while True:
    try:
        response = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for update in response.get("result", []):
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            text = message.get("text", "")
            chat_id = message["chat"]["id"]

            if text == "/start":
                requests.post(
                    f"{API}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": "🤖 Bot Online!"
                    }
                )

            elif text == "/unbanall":
                requests.post(
                    f"{API}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": "⚙️ Unban All command received."
                    }
                )

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
