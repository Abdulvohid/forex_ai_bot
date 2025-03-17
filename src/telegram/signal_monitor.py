import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot

if __name__ == "__main__" and __package__ is None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import MetaTrader5 as mt5
from src.utils.data_fetcher_mt5 import fetch_mt_data
from src.utils.mongodb_connector import signals_collection

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)

def check_signals():
    """MongoDB ichidagi status='active' signallarni bozor narxiga nisbatan TP/SL kuzatish."""
    if not mt5.initialize():
        print("[MT5] initialize xato:", mt5.last_error())
        return

    df_market = fetch_mt_data(
        symbol="GBPUSD",
        timeframe=mt5.TIMEFRAME_H1,
        start_date=datetime.now() - timedelta(days=2),
        end_date=datetime.now()
    )
    mt5.shutdown()

    if df_market.empty:
        print("[signal_monitor] Market data bo'sh, kuzatish to'xtatildi.")
        return

    current_price = df_market.iloc[-1]["close"]

    # 2. MongoDB'dan status='active' bo'lgan signallarni o'qish
    active_signals = signals_collection.find({"status": "active"})

    for signal in active_signals:
        signal_number = signal.get("signal_number")
        signal_type = signal.get("type")
        tp_price = signal.get("tp_price")
        sl_price = signal.get("sl_price")

        if tp_price is None or sl_price is None:
            print(f"Signal #{signal_number} da tp_price/sl_price maydoni topilmadi.")
            continue

        # 3. TP sharti
        if (
            (signal_type == "BUY" and current_price >= tp_price) or
            (signal_type == "SELL" and current_price <= tp_price)
        ):
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
        elif (
            (signal_type == "BUY" and current_price <= sl_price) or
            (signal_type == "SELL" and current_price >= sl_price)
        ):
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
