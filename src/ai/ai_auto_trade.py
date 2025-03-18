# FILE: src/ai/ai_auto_trade.py

import os
import time
from datetime import datetime
import pandas as pd
import joblib
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Indikator funksiyalari (real vaqtda hisoblash misol, xohlasangiz DB'dan olasiz)
from src.indicators.indicators import (
    calculate_ema, calculate_rsi, calculate_adx, calculate_atr, calculate_macd
)

load_dotenv()

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH")

MODEL_PATH = "gbpusd_model.pkl"  # Avval train qilingan AI model
SYMBOL = "GBPUSD"                # brokerda "GBPUSDz" yoki boshqacha bo'lishi mumkin
TIMEFRAME = mt5.TIMEFRAME_M15    # Har 15 daqiqada bar tugashi
LOT_SIZE = 0.07                  # Har bir bitim lot
NUM_TRADES = 4                   # Bir signalga 4 ta bitim
SL_LIMIT = -30.0                 # –30$ zarar bo‘lsa SL
TP_LIMIT = 50.0                  # +50$ foyda bo‘lsa TP

def connect_mt5():
    """MetaTrader5 ga ulanadi."""
    if not mt5.initialize(path=MT5_PATH):
        print("MT5 initialize xato:", mt5.last_error())
        return False
    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("MT5 login xato:", mt5.last_error())
        mt5.shutdown()
        return False
    print("[MT5] Ulanish OK.")
    return True

def get_open_positions(symbol):
    """Mazkur symbol bo'yicha ochiq bitimlarni qaytaradi."""
    positions = mt5.positions_get(symbol=symbol)
    return positions if positions else []

def calculate_total_profit(symbol):
    """Symbol bo'yicha jamlama PnL (profit)ni qaytaradi."""
    positions = get_open_positions(symbol)
    total_pnl = 0.0
    for pos in positions:
        total_pnl += pos.profit
    return total_pnl

def close_all_positions(symbol):
    """Symbol bo'yicha barcha ochiq bitimlarni yopish."""
    positions = get_open_positions(symbol)
    for pos in positions:
        # Pozitsiyani yopish uchun "close" order yuboramiz
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "Close by AI",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }
        result = mt5.order_send(close_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[close_all_positions] Xato retcode={result.retcode}, comment={result.comment}")
        else:
            print(f"[close_all_positions] Pozitsiya yopildi => Ticket {pos.ticket}, vol={pos.volume}, ret={result.retcode}")

def open_multi_trades(symbol, lot, n=4, deviation=10, order_type=mt5.ORDER_TYPE_BUY):
    """Bitta signalga n ta bitim ochish."""
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("[open_multi_trades] Tick topilmadi.")
        return

    if order_type == mt5.ORDER_TYPE_BUY:
        price = tick.ask
    else:
        price = tick.bid

    for i in range(n):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": deviation,
            "magic": 123456,
            "comment": "AI auto trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[open_multi_trades] Xato retcode={result.retcode}, comment={result.comment}")
        else:
            print(f"[open_multi_trades] Bitim ochildi => Ticket: {result.order}")

def main_loop():
    # 1) Modelni yuklaymiz
    model = joblib.load(MODEL_PATH)
    print("[AI] Model yuklandi:", MODEL_PATH)

    while True:
        # 2) Agar oldin ochiq bitim bo'lsa => PnL ni tekshiramiz (TP/SL)
        positions = get_open_positions(SYMBOL)
        if positions:
            total_pnl = calculate_total_profit(SYMBOL)
            print(f"[{SYMBOL}] Ochiq bitimlar => jamlama PnL = {total_pnl:.2f}$")

            if total_pnl >= TP_LIMIT:
                close_all_positions(SYMBOL)
                print(f"[{SYMBOL}] => TP urildi, +{total_pnl:.2f}$ => all closed.")
            elif total_pnl <= SL_LIMIT:
                close_all_positions(SYMBOL)
                print(f"[{SYMBOL}] => SL urildi, {total_pnl:.2f}$ => all closed.")
            else:
                # Ochiq bitimni ushlab turamiz
                pass

        else:
            # 3) Agar ochiq bitim yo'q => AI signal
            bars_needed = 50
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, bars_needed)
            if rates is None or len(rates)==0:
                print(f"[{SYMBOL}] copy_rates bo'sh, {mt5.last_error()}")
                time.sleep(1)
                continue

            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df.sort_values("time", inplace=True, ignore_index=True)

            # 4) Indikatorlarni 7 feature bilan hisoblash, shu jumladan MACD_hist
            df["EMA_5"] = calculate_ema(df, period=5, column="close")
            df["EMA_9"] = calculate_ema(df, period=9, column="close")
            df["EMA_20"] = calculate_ema(df, period=20, column="close")
            df["RSI_14"] = calculate_rsi(df, period=14, column="close")
            df["ADX"] = calculate_adx(df, period=14)
            df["ATR"] = calculate_atr(df, period=14)

            # MACD
            from src.indicators.indicators import calculate_macd
            macd_val, macd_sig, macd_hist = calculate_macd(df, column="close")
            df["MACD_hist"] = macd_hist

            # 7 feature
            feats = ["EMA_5","EMA_9","EMA_20","RSI_14","ADX","ATR","MACD_hist"]
            row = df.iloc[-1]
            X = pd.DataFrame([row[feats].values], columns=feats)

            pred_class = model.predict(X)[0]  # "BUY"/"SELL"/"HOLD"
            print(f"[AI] => {pred_class}  time={row['time']}")

            if pred_class=="BUY":
                open_multi_trades(SYMBOL, lot=LOT_SIZE, n=NUM_TRADES, order_type=mt5.ORDER_TYPE_BUY)
            elif pred_class=="SELL":
                open_multi_trades(SYMBOL, lot=LOT_SIZE, n=NUM_TRADES, order_type=mt5.ORDER_TYPE_SELL)
            else:
                print("[AI] HOLD => bitim ochmaymiz.")

        # 5) Har 1 soniyada tekshirish (demo)
        time.sleep(1)

def main():
    if not mt5.initialize(path=MT5_PATH):
        print("initialize xato:", mt5.last_error())
        return
    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("login xato:", mt5.last_error())
        mt5.shutdown()
        return
    print("[MT5] Ulanish OK.")

    main_loop()
    mt5.shutdown()

if __name__=="__main__":
    main()