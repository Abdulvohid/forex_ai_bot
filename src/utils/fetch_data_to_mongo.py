import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import MetaTrader5 as mt5

# data_fetcher_mt5.py ni import
from src.utils.data_fetcher_mt5 import fetch_mt_data

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[MongoDB] MONGO_URI topilmadi, .env faylini tekshiring.")
    exit()

client = MongoClient(MONGO_URI)
db = client["forex_signals"]  # Bazaning nomi

def main():
    # 1) Parametrlar
    symbol = "GBPUSD"            # Brokerda “GBPUSDz”, “GBPUSD.m” bo‘lishi mumkin
    timeframe_label = "H1"       # Kolleksiya nomiga qulay
    timeframe_code = mt5.TIMEFRAME_H1

    start_date = datetime(2022,1,1)
    end_date   = datetime(2023,1,1)

    # 2) MetaTrader5’dan data
    df = fetch_mt_data(
        symbol=symbol,
        timeframe=timeframe_code,
        start_date=start_date,
        end_date=end_date
    )
    if df.empty:
        print(f"[{symbol} {timeframe_label}] => DF bo'sh. Yuklanmadi.")
        return

    # 3) Mongo kolleksiya nomi
    coll_name = f"{symbol}_{timeframe_label}"  # "GBPUSD_H1"
    collection = db[coll_name]

    # Avval o‘chirib tashlash (ixtiyoriy, test uchun)
    collection.delete_many({})
    print(f"[MongoDB] '{coll_name}' kolleksiyasi tozalandi.")

    # 4) DF -> dict -> insert_many
    docs = df.to_dict("records")
    result = collection.insert_many(docs)
    print(f"[MongoDB] {len(result.inserted_ids)} hujjat '{coll_name}' ga qo'shildi.")

    # MT5'ni yopish
    mt5.shutdown()

if __name__ == "__main__":
    main()