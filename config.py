import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

DEFAULT_AD_INTERVAL_HOURS = float(
    os.getenv("DEFAULT_AD_INTERVAL_HOURS", "24")
)
