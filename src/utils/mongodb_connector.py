# src/utils/mongodb_connector.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 1. MONGODB_URI ni .env faylidan o‘qish
MONGODB_URI = os.getenv("MONGODB_URI")

# 2. MongoClient bilan ulanish
client = MongoClient(MONGODB_URI)

# 3. Bazani ochish (forex_signals) va collection (signals)
db = client["forex_signals"]
signals_collection = db["signals"]

def insert_signal(signal_data):
    """
    Yangi signal hujjatini 'signals' collection'ga qo‘shadi.
    """
    signals_collection.insert_one(signal_data)

def signal_exists(signal_number):
    """
    Berilgan 'signal_number' dagi hujjat bazada bormi-yo‘qligini tekshiradi.
    """
    doc = signals_collection.find_one({"signal_number": signal_number})
    return doc is not None

def get_last_signal_number():
    """
    signals collection'dagi eng katta signal_number qiymatini qaytaradi.
    Agar hech narsa bo‘lmasa, 0 qaytaradi.
    """
    last_signal = signals_collection.find_one(sort=[("signal_number", -1)])
    if last_signal:
        return last_signal["signal_number"]
    return 0