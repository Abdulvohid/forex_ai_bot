import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["forex_signals"]
    collections = db.list_collection_names()
    print("MongoDB collections:", collections)
except Exception as e:
    print("MongoDB connection error:", e)