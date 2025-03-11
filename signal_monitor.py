import pandas as pd
from datetime import datetime
from data_fetcher import fetch_forex_data
from telegram import Bot
import os

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=bot_token)

def check_signals():
    try:
        df_signals = pd.read_csv('active_signals.csv')
    except FileNotFoundError:
        print("active_signals.csv mavjud emas.")
        return
    
    # Bozor narxlarini olamiz (oxirgi close)
    df_market = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=1)
    current_price = df_market.iloc[-1]['close']
    
    for index, row in df_signals.iterrows():
        if row['status'] == 'active':
            signal_number = int(row['signal_number'])
            entry_price = float(row['entry_price'])
            tp_price = float(row['tp_price'])
            sl_price = float(row['sl_price'])
            signal_type = row['type']
            
            # TP yoki SL urilganligini tekshiramiz
            if (signal_type == 'BUY' and current_price >= tp_price) or (signal_type == 'SELL' and current_price <= tp_price):
                # TP olindi
                bot.send_message(chat_id=chat_id, text=f"Signal #{signal_number} TP olindi ✅\nHozirgi narx: {current_price}")
                df_signals.at[index, 'status'] = 'closed'
                df_signals.at[index, 'close_time'] = str(datetime.now())
            
            elif (signal_type == 'BUY' and current_price <= sl_price) or (signal_type == 'SELL' and current_price >= sl_price):
                # SL urildi
                bot.send_message(chat_id=chat_id, text=f"Signal #{signal_number} SL urildi ❌\nHozirgi narx: {current_price}")
                df_signals.at[index, 'status'] = 'closed'
                df_signals.at[index, 'close_time'] = str(datetime.now())
    
    df_signals.to_csv('active_signals.csv', index=False)

if __name__ == "__main__":
    check_signals()