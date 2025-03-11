import os
from dotenv import load_dotenv
from telegram import Bot
from data_fetcher import fetch_forex_data
from indicators import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_stochastic,
    calculate_adx, calculate_atr
)
from strategy import generate_trade_signals
from ai_model import predict_signal
from predict_tp_sl import predict_tp_sl
import time
import pandas as pd
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

signal_counter_file = "signal_counter.txt"

def main():
    # 1) Forex ma'lumotlarini olish
    df = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=5000)

    # 2) Indikatorlarni hisoblash
    df['EMA_14'] = calculate_ema(df, period=14)
    df['RSI_14'] = calculate_rsi(df, period=14)
    df['MACD'], df['MACD_signal'], df['MACD_histogram'] = calculate_macd(df)
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df)
    df['Stoch_%K'], df['Stoch_%D'] = calculate_stochastic(df)
    df['ADX'] = calculate_adx(df)
    df['ATR'] = calculate_atr(df)
    
    # 3) Strategiya (oddiy signallar)
    df = generate_trade_signals(df)
    latest_row = df.iloc[-1]

    # 4) AI modeli bilan signal
    predicted_signal, probability = predict_signal(latest_row)

    # Faqat 70%+ aniqlik va HOLD bo'lmagan signal yuboriladi
    if predicted_signal == 'HOLD' or probability < 0.7:
        print(f"Signal: {predicted_signal}, Aniqlik: {probability*100:.1f}% - Yuborilmadi.")
        return

    # 5) TP/SL narxlarini hisoblash
    tp_price, sl_price = predict_tp_sl(latest_row, predicted_signal)

    # 6) Signal raqamini aniqlash
    if os.path.exists(signal_counter_file):
        with open(signal_counter_file, "r") as f:
            signal_number = int(f.read().strip()) + 1
    else:
        signal_number = 1

    with open(signal_counter_file, "w") as f:
        f.write(str(signal_number))

    # 🔔 Vaqtni kompyuter vaqti qilib ko'rsatamiz
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 7) Xabar matni
    message = (
        f"📊 Valyuta juftligi: GBP/USD (H1)\n"
        f"🕒 Vaqt: {current_time}\n"  # Kompyuter (hozirgi) vaqti
        f"📍 Joriy narx: {latest_row['close']:.5f}\n"
        f"📌 Signal: {predicted_signal}\n"
        f"🎯 Take Profit (TP): {tp_price:.5f}\n"
        f"🛡 Stop Loss (SL): {sl_price:.5f}\n"
        f"📈 AI aniqligi: {min(probability*100, 95.0):.1f}%\n"
        f"🔢 Signal raqami: #{signal_number}"
    )

    bot.send_message(chat_id=CHAT_ID, text=message)
    print("Telegramga signal yuborildi ->", message)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(600)  # 10 daqiqa = 600 soniya