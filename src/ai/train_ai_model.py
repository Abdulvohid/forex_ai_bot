import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
import joblib

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[train_ai_model] MONGO_URI topilmadi. .env ni tekshiring.")
    exit()

client = MongoClient(MONGO_URI)
db = client["forex_signals"]

def main():
    coll_name = "GBPUSD_H1_full"
    docs = list(db[coll_name].find())
    if not docs:
        print(f"[train_ai_model] {coll_name} bo'sh!")
        return

    df = pd.DataFrame(docs)
    if "_id" in df.columns:
        df.drop("_id", axis=1, inplace=True)

    df["time"] = pd.to_datetime(df["time"])
    df.sort_values("time", inplace=True, ignore_index=True)
    print(f"[train_ai_model] {coll_name} => {len(df)} satr.")

    # 7 ustun: EMA_5, EMA_9, EMA_20, RSI_14, ATR, ADX, MACD_hist
    feats = ["EMA_5","EMA_9","EMA_20","RSI_14","ATR","ADX","MACD_hist"]
    for f in feats:
        if f not in df.columns:
            print(f"[train_ai_model] Ustun '{f}' topilmadi. Indikatorni tekshiring.")
            return

    # Label (Signal) - misol BUY/SELL/HOLD
    df["Signal"] = "HOLD"
    # Soddalashtirilgan - (EMA_5>EMA_9>EMA_20 & RSI>50 & ADX>20 => BUY), (aksincha => SELL)
    df.loc[
        (df["EMA_5"] > df["EMA_9"]) &
        (df["EMA_9"] > df["EMA_20"]) &
        (df["RSI_14"] > 50) &
        (df["ADX"] > 20),
        "Signal"
    ] = "BUY"

    df.loc[
        (df["EMA_5"] < df["EMA_9"]) &
        (df["EMA_9"] < df["EMA_20"]) &
        (df["RSI_14"] < 50) &
        (df["ADX"] > 20),
        "Signal"
    ] = "SELL"

    # X,y
    X = df[feats]
    y = df["Signal"]

    combined = pd.concat([X,y], axis=1).dropna()
    X = combined[feats]
    y = combined["Signal"]

    print(f"[train_ai_model] X.shape={X.shape}, y.shape={y.shape}, classes={y.unique()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = LGBMClassifier(
        n_estimators=300,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[train_ai_model] Aniqlik: {acc*100:.2f}%")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, "gbpusd_model.pkl")
    print("[train_ai_model] Model 'gbpusd_model.pkl' saqlandi.")

if __name__=="__main__":
    main()
