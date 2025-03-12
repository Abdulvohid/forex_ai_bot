import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWELVE_DATA_API_KEY")  # Alpha Vantage yoki TwelveData kaliti

def fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=500):
    """Twelve Data API yoki Alpha Vantage API orqali ma'lumot oladi."""
    base_url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": outputsize
    }
    resp = requests.get(base_url, params=params).json()
    if "values" in resp:
        df = pd.DataFrame(resp["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)
        df.reset_index(drop=True, inplace=True)
        return df
    else:
        raise ValueError(f"API xato yoki ma'lumot yo'q: {resp}")