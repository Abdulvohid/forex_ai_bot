import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot

# 1) Skript rejimida ishga tushganda "src" papkasini top-level package sifatida tanitish
if __name__ == "__main__" and __package__ is None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# 2) "src" importlarini xatosiz bajarish
from src.utils.data_fetcher import fetch_forex_data
from src.utils.mongodb_connector import signals_collection

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)

def check_signals():
    """MongoDB ichidagi status='active' signallarni bozor narxiga nisbatan TP/SL kuzatish."""
    # 1. So'nggi bozor narxini olish (masalan, GBP/USD, H1)
    df_market = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=1)
    current_price = df_market.iloc[-1]["close"]

    # 2. MongoDB'dan status='active' bo'lgan signallarni o'qish
    active_signals = signals_collection.find({"status": "active"})

    for signal in active_signals:
        # Kutilayotgan maydonlar: signal_number, type, tp_price, sl_price
        # Ba'zi signallarda tp_price/sl_price bo'lmasligi mumkin, shuning uchun get() ishlatamiz
        signal_number = signal.get("signal_number")
        signal_type = signal.get("type")
        tp_price = signal.get("tp_price")
        sl_price = signal.get("sl_price")

        # Agar tp_price yoki sl_price hujjatda bo'lmasa, e'tiborsiz qoldiramiz
        if tp_price is None or sl_price is None:
            print(f"Signal #{signal_number} da tp_price/sl_price maydoni topilmadi.")
            continue

        # 3. TP sharti
        if (signal_type == "BUY" and current_price >= tp_price) or \
           (signal_type == "SELL" and current_price <= tp_price):

            bot.send_message(
                chat_id=chat_id,
                text=f"Signal #{signal_number} TP olindi ✅\nHozirgi narx: {current_price}"
            )
            signals_collection.update_one(
                {"signal_number": signal_number},
                {"$set": {
                    "status": "closed",
                    "close_time": datetime.now()
                }}
            )
            print(f"Signal #{signal_number} TP ga yetdi, status=closed")

        # 4. SL sharti
        elif (signal_type == "BUY" and current_price <= sl_price) or \
             (signal_type == "SELL" and current_price >= sl_price):

            bot.send_message(
                chat_id=chat_id,
                text=f"Signal #{signal_number} SL urildi ❌\nHozirgi narx: {current_price}"
            )
            signals_collection.update_one(
                {"signal_number": signal_number},
                {"$set": {
                    "status": "closed",
                    "close_time": datetime.now()
                }}
            )
            print(f"Signal #{signal_number} SL urildi, status=closed")

if __name__ == "__main__":
    check_signals()