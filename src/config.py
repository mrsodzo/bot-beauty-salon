from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "salon.db"))
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
PORT = int(os.getenv("PORT", "8080"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

SALON_NAME = "Barber Studio"
SALON_ADDRESS = "ул. Примерная, д. 1"
SALON_PHONE = "+7 (999) 000-00-00"
WORK_START = 10
WORK_END = 19
INTERVAL = 60
