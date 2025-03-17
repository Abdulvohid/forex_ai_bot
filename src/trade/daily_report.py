# FILE: src/trade/daily_report.py

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.mongodb_connector import signals_collection

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

def main():
    now = datetime.now()
    since_time = now - timedelta(hours=24)
    closed_signals = list(signals_collection.find({
        "status": "closed",
        "close_time": {"$gte": since_time}
    }))

    if not closed_signals:
        print("[daily_report] So'nggi 24 soatda yopilgan signal yo'q.")
        return

    tp_count = sum(1 for s in closed_signals if s.get("result")=="TP")
    sl_count = sum(1 for s in closed_signals if s.get("result")=="SL")

    msg = (
        f"🗓 Kunlik hisobot (oxirgi 24 soat):\n"
        f"Yopilgan signallar soni: {len(closed_signals)}\n"
        f"TP bo'lgan: {tp_count}\n"
        f"SL bo'lgan: {sl_count}\n"
        f"Vaqt: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    bot.send_message(chat_id=CHAT_ID, text=msg)
    print("[daily_report] Telegram xabar yuborildi:\n", msg)

if __name__=="__main__":
    main()