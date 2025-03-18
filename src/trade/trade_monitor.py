# FILE: src/trade/trade_monitor.py

import time
import os
# <<<<< Yangi import >>>>>
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Bot
import MetaTrader5 as mt5

from src.utils.mongodb_connector import signals_collection
from src.utils.data_fetcher_mt5 import fetch_mt_data

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
bot       = Bot(token=BOT_TOKEN)

MT5_LOGIN    = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER   = os.getenv("MT5_SERVER", "")
MT5_PATH     = os.getenv("MT5_PATH", "")

# <<<<< Yangi import: import "last_close_time" lug'ati >>>>>
from src.trade.live_demo_trading import last_close_time

def initialize_mt5():
    if not mt5.initialize(path=MT5_PATH):
        print("[MT5] initialize xato:", mt5.last_error())
        return False
    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("[MT5] login xato:", mt5.last_error())
        mt5.shutdown()
        return False
    print("[MT5] Ulanish OK. Balans:", mt5.account_info().balance)
    return True

def check_signals():
    if not initialize_mt5():
        return

    # Masalan, faqat GBPUSD bo'yicha narxni olamiz
    df_market = fetch_mt_data(
        symbol="GBPUSD",
        timeframe=mt5.TIMEFRAME_H1,
        start_date=datetime.now() - timedelta(days=2),
        end_date=datetime.now()
    )
    mt5.shutdown()

    if df_market.empty:
        print("[trade_monitor] Market data bo'sh, kuzatish to'xtatildi.")
        return

    current_price = df_market.iloc[-1]["close"]
    active_signals = signals_collection.find({"status": "active"})

    for signal in active_signals:
        signal_number = signal.get("signal_number")
        signal_type   = signal.get("type")       # BUY/SELL
        tp_price      = signal.get("tp_price")
        sl_price      = signal.get("sl_price")
        symbol        = signal.get("symbol")     # Qaysi symbol ?

        if not symbol or tp_price is None or sl_price is None:
            continue

        # Biz hozir GBPUSD narxini oldik. Agar symbol GBPUSD bo'lsa, uni check.
        # Boshqa symbol-larni ham xohlasak, fetch_mt_data(..., symbol=signal["symbol"]) har biriga ishlashimiz kerak
        # Yoki bevosita 'tick = mt5.symbol_info_tick(symbol)' bilan check qilsak bo'ladi.

        # Misol uchun bevosita tick bilan (aniq):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        current_price_symbol = tick.ask if signal_type=="BUY" else tick.bid

        # TP
        if ((signal_type=="BUY" and current_price_symbol>=tp_price) or
            (signal_type=="SELL" and current_price_symbol<=tp_price)):
            bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔆 Signal #{signal_number} ({symbol}) => TP ✅\nNarx: {current_price_symbol:.5f}"
            )
            signals_collection.update_one(
                {"signal_number": signal_number},
                {"$set": {"status": "closed", "close_time": datetime.now()}}
            )
            print(f"Signal #{signal_number} => TP closed")

            # <<<<< Muhim: endi 30 daqiqa cooldown faqat shu symbol >>>>>
            last_close_time[symbol] = datetime.now()

        # SL
        elif ((signal_type=="BUY" and current_price_symbol<=sl_price) or
              (signal_type=="SELL" and current_price_symbol>=sl_price)):
            bot.send_message(
                chat_id=CHAT_ID,
                text=f"🌑 Signal #{signal_number} ({symbol}) => SL ❌\nNarx: {current_price_symbol:.5f}"
            )
            signals_collection.update_one(
                {"signal_number": signal_number},
                {"$set": {"status": "closed", "close_time": datetime.now()}}
            )
            print(f"Signal #{signal_number} => SL closed")

            # <<<<< Symbol uchun 30 daqiqa pauza >>>>>
            last_close_time[symbol] = datetime.now()

def main_loop():
    while True:
        check_signals()
        time.sleep(60)

if __name__ == "__main__":
    main_loop()