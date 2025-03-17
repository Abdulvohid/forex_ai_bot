# FILE: src/utils/mongodb_connector.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["forex_signals"]

signals_collection = db["signals"]

def signal_exists(signal_number: int) -> bool:
    """Mazkur signal_number bilan oldin signal yuborilganmi-yo'qmi tekshiradi."""
    existing = signals_collection.find_one({"signal_number": signal_number})
    return existing is not None

def get_last_signal_number() -> int:
    last_signal = signals_collection.find_one(sort=[("signal_number", -1)])
    return last_signal["signal_number"] if last_signal else 0

def insert_signal(signal_data: dict):
    """Yangi signal hujjatini 'signals' kolleksiyasiga kiritish."""
    signals_collection.insert_one(signal_data)
    print(f"[MongoDB] Signal #{signal_data['signal_number']} bazaga qo'shildi.")