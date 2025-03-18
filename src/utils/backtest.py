import os
import pandas as pd
import joblib
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[Backtest] MONGO_URI topilmadi, .env ni tekshiring.")
    exit()

client = MongoClient(MONGO_URI)
db = client["forex_signals"]

MODEL_PATH = "gbpusd_model.pkl"
SYMBOL_COLLECTION = "GBPUSD_H1_full"

# Parametrlar
NUM_TRADES = 4
TP_LIMIT = 50.0   # +50$ jamlama
SL_LIMIT = -30.0  # –30$ jamlama

def main():
    # 1) Data yuklash
    docs = list(db[SYMBOL_COLLECTION].find())
    if not docs:
        print(f"[Backtest] {SYMBOL_COLLECTION} bo'sh.")
        return
    df = pd.DataFrame(docs)
    if "_id" in df.columns:
        df.drop("_id", axis=1, inplace=True)

    df["time"] = pd.to_datetime(df["time"])
    df.sort_values("time", inplace=True, ignore_index=True)
    print(f"[Backtest] {len(df)} satr yuklandi => {SYMBOL_COLLECTION}")

    # 2) Model yuklash
    model = joblib.load(MODEL_PATH)
    print("[Backtest] Model yuklandi:", MODEL_PATH)

    # 3) Featurelar
    feats = ["EMA_5","EMA_9","EMA_20","RSI_14","ADX","ATR","MACD_hist"]
    for f in feats:
        if f not in df.columns:
            print(f"[Backtest] {f} ustuni topilmadi. Indikatorni to'g'ri hisoblang.")
            return

    # 4) Virtual trade parametrlari
    balance = 1000.0  # misol, 1000$ start
    open_position = False
    position_side = None  # "BUY" yoki "SELL"
    entry_price = None
    trade_pnl = 0.0
    total_closed_pnl = 0.0
    trade_count = 0

    # jamlama bitim => 4 ta
    # Biz soddalashtirib "lot" masalasini e'tibor qilmadik,
    # shunchaki har 1$ narx o'zgarishiga N$ o'zgarish bo'ladi deb faraz qilamiz.
    # Yoki real pips / volume hisobi kerak bo'ladi.

    # 5) Barma-bar yurish
    for i in range(len(df)):
        row = df.iloc[i]
        X = pd.DataFrame([row[feats].values], columns=feats)
        pred = model.predict(X)[0]  # "BUY"/"SELL"/"HOLD"

        if not open_position:
            # Agar ochiq bitim yo'q bo'lsa => agar BUY/SELL chiqsa => 4 ta bitim ochamiz (virtual)
            if pred in ["BUY","SELL"]:
                open_position = True
                position_side = pred
                entry_price = row["close"]  # soddalashtirilgan
                trade_pnl = 0.0
                trade_count += 1
                print(f"[i={i}] => {pred} ochildi! time={row['time']} price={entry_price:.5f}")
        else:
            # Agar ochiq bitim bor => jamlama PnL tekshiramiz
            # (Narx farq * 4 trades) => soddalashtirish
            current_price = row["close"]
            # soddalashtirilgan pips hisobi
            if position_side=="BUY":
                # farq = (current_price - entry_price)
                # jamlama => farq * 4 (virtual)
                trade_pnl = (current_price - entry_price)*4000.0  # misol, multiplikatsiya (o'zb)
            else:
                # SELL => farq teskari
                trade_pnl = (entry_price - current_price)*4000.0

            # PnLga qarab TP/SL
            if trade_pnl >= TP_LIMIT:
                print(f"[i={i}] => TP oldi, +{trade_pnl:.2f}$ time={row['time']}")
                balance += trade_pnl
                total_closed_pnl += trade_pnl
                open_position = False
                position_side = None
                entry_price = None
            elif trade_pnl <= SL_LIMIT:
                print(f"[i={i}] => SL urildi, {trade_pnl:.2f}$ time={row['time']}")
                balance += trade_pnl
                total_closed_pnl += trade_pnl
                open_position = False
                position_side = None
                entry_price = None

    # 6) Yakuniy natija
    if open_position:
        # Oxirgi bar bo'lsa-yu bitim yopilmagan bo'lsa
        # Yopilgan deb faraz qilamiz (tugadi)
        final_price = df.iloc[-1]["close"]
        if position_side=="BUY":
            trade_pnl = (final_price - entry_price)*4000.0
        else:
            trade_pnl = (entry_price - final_price)*4000.0
        balance += trade_pnl
        total_closed_pnl += trade_pnl
        print(f"[Backtest] Oxirgi bitim yopildi => PnL={trade_pnl:.2f}$")

    print(f"[Backtest] Yakuniy balance={balance:.2f}, total_closed_pnl={total_closed_pnl:.2f}")
    print(f"[Backtest] {trade_count} ta trade qilindi.")
    print("[Backtest] Tugadi.")

if __name__=="__main__":
    main()