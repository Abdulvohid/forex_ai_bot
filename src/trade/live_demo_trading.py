import os
import time
from datetime import datetime, timedelta

import MetaTrader5 as mt5
from dotenv import load_dotenv
import joblib
import telegram

from src.utils.data_fetcher_mt5 import fetch_mt_data
from src.utils.mongodb_connector import signals_collection, insert_signal
from src.indicators.indicators import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_adx, calculate_atr
)
# trade_manager => place_order(...) butun 'result' obyektini qaytaradi
from src.trade.trade_manager import place_order

load_dotenv()

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
bot       = telegram.Bot(token=BOT_TOKEN)

MODEL_PATH       = "gbpusd_model.pkl"
model            = joblib.load(MODEL_PATH)
model_classes    = model.classes_

########################################################################
# Har symbol uchun SL/TP pip (masalan XAUUSD=5/7, BTCUSD=5/7, boshqalar=15/25)
########################################################################
custom_sl_tp = {
    "BTCUSD": (5, 7),
    "XAUUSD": (5, 7),
    "US500":  (5, 10),
    "USTEC":  (5, 10),
    "XAUEUR": (5, 7),
    "XAUGBP": (5, 7)
}

symbol_pips_map = {
    "GBPUSD": 0.0001,
    "XAUUSD": 1.0,
    "BTCUSD": 20.0,
    "US500":  0.1,
    "USTEC":  0.1,
    "EURUSD": 0.0001,
    "USDJPY": 0.01,
    "XAUEUR": 0.1,
    "XAUGBP": 0.1
}

# Kunlik limit
DAILY_LOSS_LIMIT  = -200.0
DAILY_PROFIT_LIMIT=  500.0

########################################################################
# LUG'AT SHAKLINDA => last_close_time[symbol] = datetime
# trade_monitor.py da bitim yopilganda update qilinadi
########################################################################
last_close_time = {}

def get_today_pnl():
    now = datetime.now()
    today_00 = datetime(now.year, now.month, now.day, 0,0,0)
    closed_signals = signals_collection.find({
        "status":"closed",
        "close_time": {"$gte": today_00}
    })
    total_pnl=0.0
    for s in closed_signals:
        total_pnl += s.get("profit",0.0)
    return total_pnl

def initialize_mt5():
    if not mt5.initialize(path=MT5_PATH):
        print("[MT5] init xato:", mt5.last_error())
        return False
    ok=mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not ok:
        print("[MT5] login xato:", mt5.last_error())
        mt5.shutdown()
        return False
    acc=mt5.account_info()
    if acc:
        print("[MT5] Ulanish OK. Balans:", acc.balance)
    return True

def add_indicators(df):
    df["EMA_5"] = calculate_ema(df, period=5)
    df["EMA_9"] = calculate_ema(df, period=9)
    df["EMA_20"] = calculate_ema(df, period=20)
    df["RSI_14"] = calculate_rsi(df, period=14)
    df["MACD"], macd_signal, macd_hist = calculate_macd(df)
    df["MACD_signal"] = macd_signal
    df["MACD_hist"]  = macd_hist
    df["ADX"] = calculate_adx(df)
    df["ATR"] = calculate_atr(df, period=14)
    return df

def has_open_position_for_symbol(symbol):
    pos=mt5.positions_get(symbol=symbol)
    return bool(pos)

def open_new_trades():
    daily_pnl = get_today_pnl()
    if daily_pnl <= DAILY_LOSS_LIMIT:
        print(f"[open_new_trades] Kunlik zarar {daily_pnl:.2f} <= {DAILY_LOSS_LIMIT}, bugun savdo qilmaymiz.")
        return
    if daily_pnl >= DAILY_PROFIT_LIMIT:
        print(f"[open_new_trades] Kunlik foyda {daily_pnl:.2f} >= {DAILY_PROFIT_LIMIT}, bugun savdo qilmaymiz.")
        return

    symbols=["GBPUSD","XAUUSD","BTCUSD","US500","USTEC","EURUSD","USDJPY","XAUEUR","XAUGBP"]

    for symbol in symbols:
        # 1) Symbol bo'yicha 30 daq cooldown
        if symbol in last_close_time:
            diff = (datetime.now() - last_close_time[symbol]).total_seconds()
            if diff < 1800:
                print(f"[{symbol}] => last close was {diff:.1f}s ago => skip (30min).")
                continue

        # 2) Agar shu symbol open bo'lsa => skip
        if has_open_position_for_symbol(symbol):
            print(f"[{symbol}] => oldin open => skip.")
            continue

        # 3) Data
        df = fetch_mt_data(
            symbol=symbol,
            timeframe=mt5.TIMEFRAME_M1,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        if df.empty or len(df)<10:
            print(f"[{symbol}] => data kam or empty.")
            continue

        df=add_indicators(df)
        df.dropna(inplace=True)
        if df.empty:
            continue

        last_row = df.iloc[-1]
        feats    = ["EMA_5","EMA_9","EMA_20","RSI_14","ATR","ADX","MACD_hist"]
        X        = last_row[feats].values.reshape(1,-1)

        pred = model.predict(X)[0]
        proba= model.predict_proba(X)[0]
        if pred not in model_classes:
            continue
        idx  = list(model_classes).index(pred)
        conf = proba[idx]
        if conf<0.70 or pred not in ["BUY","SELL"]:
            print(f"[{symbol}] => conf={conf*100:.1f}% or pred={pred}, skip.")
            continue

        # 4) SL/TP
        default_sl, default_tp = (15,25)
        if symbol in custom_sl_tp:
            default_sl, default_tp = custom_sl_tp[symbol]

        pip = symbol_pips_map.get(symbol, 0.0001)
        sl_dist = default_sl*pip
        tp_dist = default_tp*pip

        cprice = last_row["close"]
        if pred=="BUY":
            sl_price = cprice - sl_dist
            tp_price = cprice + tp_dist
        else:
            sl_price = cprice + sl_dist
            tp_price = cprice - tp_dist

        sinfo=mt5.symbol_info(symbol)
        if sinfo:
            min_stop = sinfo.trade_stops_level*sinfo.point
            if abs(cprice-sl_price)<min_stop:
                if pred=="BUY":
                    sl_price = cprice - (min_stop*10)
                else:
                    sl_price = cprice + (min_stop*10)
            if abs(cprice-tp_price)<min_stop:
                if pred=="BUY":
                    tp_price = cprice + (min_stop*10)
                else:
                    tp_price = cprice - (min_stop*10)

        # BTCUSD va XAUUSD => 0.07, boshqalar => 0.15
        if symbol in ["BTCUSD","XAUUSD", "XAUEUR", "XAUGBP"]:
            lot=0.07
        else:
            lot=0.15

        tickets=[]
        for _ in range(3):
            result=place_order(symbol, pred, lot,
                               sl_price=sl_price,
                               tp_price=tp_price,
                               comment="AI Robot with SL/TP")
            if result:
                tickets.append(result.order)

        if tickets:
            msg=(f"🔔 *Yangi bitim:* {symbol}\n"
                 f"• Signal raqami: #{int(time.time())}\n"
                 f"• Signal: {pred}, conf={conf*100:.1f}%\n"
                 f"• Narx: {cprice:.5f}\n"
                 f"• SL: {sl_price:.5f}, TP: {tp_price:.5f}")
            bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            print(msg)

            sig_num=int(time.time())
            data={
                "signal_number": sig_num,
                "symbol":symbol,
                "direction":pred,
                "time":datetime.now(),
                "lot":lot,
                "sl_price":sl_price,
                "tp_price":tp_price,
                "tickets":tickets,
                "confidence":conf,
                "status":"active"
            }
            insert_signal(data)
            print(f"[{symbol}] => DB => {sig_num}")
            return

def main():
    if not initialize_mt5():
        return

    while True:
        open_new_trades()
        # Endi "monitor_tp_sl()" bu faylda ishlatilmaydi,
        # chunki yopish "trade_monitor.py" da sodir bo'ladi.
        time.sleep(60)
        print("1 daqiqa kutamiz...")

    mt5.shutdown()

if __name__=="__main__":
    main()