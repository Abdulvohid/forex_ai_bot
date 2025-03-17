import os
from dotenv import load_dotenv
from pymongo import MongoClient

def main():
    load_dotenv()

    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("[MongoDB CLEAR] MONGO_URI topilmadi, .env faylini tekshiring.")
        return

    # MongoDB ulanish
    client = MongoClient(MONGO_URI)
    db = client["forex_signals"]

    # Barcha kolleksiyalarni topish
    collections = db.list_collection_names()
    if not collections:
        print("[MongoDB CLEAR] Hech qanday kolleksiya topilmadi.")
        return

    # Har bir kolleksiyani to'liq o'chirib tashlash (drop)
    for coll_name in collections:
        db[coll_name].drop()
        print(f"[MongoDB CLEAR] {coll_name} kolleksiyasi o'chirildi.")

    print("[MongoDB CLEAR] Barcha kolleksiyalar o'chirildi.")

if __name__ == "__main__":
    main()