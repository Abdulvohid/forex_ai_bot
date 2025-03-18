# FILE: src/utils/data_fetcher_mt5.py

import os
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH")

def connect_mt5():
    """MetaTrader5 ga ulanadi."""
    if not mt5.initialize(path=MT5_PATH):
        print("mt5.initialize xato:", mt5.last_error())
        return False
    time.sleep(2)

    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("MT5 login xato:", mt5.last_error())
        mt5.shutdown()
        return False
    print("[MT5] Ulanish OK.")
    return True

def fetch_mt_data(
    symbol="GBPUSD",                 # Default: GBPUSD
    timeframe=mt5.TIMEFRAME_H1,     # Default: H1
    start_date=datetime(2022,1,1),
    end_date=datetime(2023,1,1)
):
    """
    MetaTrader5’dan copy_rates_range orqali data olib,
    DataFrame shaklida qaytaradi. Agar xato bo'lsa -> bo'sh DF.
    """
    if not connect_mt5():
        return pd.DataFrame()

    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    if rates is None or len(rates) == 0:
        print("[MT5] copy_rates_range xato yoki bo'sh:", mt5.last_error())
        mt5.shutdown()
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.sort_values("time", inplace=True, ignore_index=True)
    print(f"[MT5] {symbol} => {len(df)} bar yuklandi. [{df['time'].iloc[0]} ~ {df['time'].iloc[-1]}]")
    return df

if __name__=="__main__":
    # Test maqsadida: GBPUSD, H1, 2022-01-01 ~ 2023-01-01
    df_test = fetch_mt_data(
        symbol="GBPUSD",               # Agar brokerda "GBPUSDz" bo'lsa, shuni yozing
        timeframe=mt5.TIMEFRAME_H1,
        start_date=datetime(2022,1,1),
        end_date=datetime(2023,1,1)
    )
    print("Barlar soni:", len(df_test))
    if not df_test.empty:
        print(df_test.head(5))
    mt5.shutdown()