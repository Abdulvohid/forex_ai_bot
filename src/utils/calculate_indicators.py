# FILE: src/utils/calculate_indicators.py

import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

from src.indicators.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_adx,
    calculate_atr
)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[CalcIndicators] MONGO_URI topilmadi, .env faylini tekshiring.")
    exit()

client = MongoClient(MONGO_URI)
db = client["forex_signals"]

def main():
    symbol_coll = "GBPUSD_H1"
    target_coll = "GBPUSD_H1_full"

    docs = list(db[symbol_coll].find())
    if not docs:
        print(f"[CalcIndicators] {symbol_coll} bo'sh!")
        return

    df = pd.DataFrame(docs)
    if "_id" in df.columns:
        df.drop("_id", axis=1, inplace=True)
    df["time"] = pd.to_datetime(df["time"])
    df.sort_values("time", inplace=True, ignore_index=True)
    print(f"[CalcIndicators] {symbol_coll} => {len(df)} satr olindi.")

    # Indikatorlar
    df["EMA_5"] = calculate_ema(df, period=5)
    df["EMA_9"] = calculate_ema(df, period=9)
    df["EMA_20"] = calculate_ema(df, period=20)

    df["RSI_14"] = calculate_rsi(df, period=14)
    macd_val, macd_sig, macd_hist = calculate_macd(df)
    df["MACD"] = macd_val
    df["MACD_signal"] = macd_sig
    df["MACD_hist"] = macd_hist

    df["ADX"] = calculate_adx(df)
    df["ATR"] = calculate_atr(df)

    # Yangi kolleksiya
    db[target_coll].delete_many({})
    docs_full = df.to_dict("records")
    db[target_coll].insert_many(docs_full)
    print(f"[CalcIndicators] {len(docs_full)} satr '{target_coll}' ga yozildi.")

if __name__=="__main__":
    main()