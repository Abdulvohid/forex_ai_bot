import os
import time
from datetime import datetime

from dotenv import load_dotenv
from telegram import Bot

from src.utils.data_fetcher import fetch_forex_data
from src.indicators.indicators import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_stochastic,
    calculate_adx, calculate_atr
)
from src.indicators.strategy import generate_trade_signals

from src.ai.ai_model import predict_signal
from src.ai.predict_tp_sl import predict_tp_sl

# MongoDB connector
from src.utils.mongodb_connector import (
    signals_collection,
    get_last_signal_number,
    signal_exists,
    insert_signal
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=BOT_TOKEN)

def main():
    # 1. Bozor data (1 soatlik GBP/USD)
    df = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=5000)

    # 2. Indikatorlar
    df['EMA_14'] = calculate_ema(df, period=14)
    df['RSI_14'] = calculate_rsi(df, period=14)
    df['MACD'], df['MACD_signal'], df['MACD_histogram'] = calculate_macd(df)
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df)
    df['Stoch_%K'], df['Stoch_%D'] = calculate_stochastic(df)
    df['ADX'] = calculate_adx(df)
    df['ATR'] = calculate_atr(df)

    # 3. Strategy signal (BUY/SELL/HOLD)
    df = generate_trade_signals(df)
    latest_row = df.iloc[-1]
    predicted_signal, probability = predict_signal(latest_row)

    # 4. --> Shart-1: Avvalgi signal hali "active" bo'lsa, yangisini yubormaymiz
    active_signal = signals_collection.find_one({
        "currency_pair": "GBP/USD",
        "status": "active"
    })
    if active_signal:
        print("Avvalgi signal hali yopilmagan (active), yangisini yubormaymiz.")
        return

    # 5. --> Shart-2: Narx yetarlicha o'zgarmagan bo'lsa, yubormaslik
    # Oxirgi signal (ENG) ni topamiz
    last_signal = signals_collection.find_one(
        {"currency_pair": "GBP/USD"},
        sort=[("signal_number", -1)]
    )

    current_price = latest_row["close"]
    if last_signal:
        old_price = last_signal["entry_price"]  # Oxirgi signalning narxi
        price_diff = abs(current_price - old_price)
        if price_diff < 0.0003:  # Masalan, 3 pip o'zgarmagan bo'lsa, skip
            print(f"Narx {price_diff:.5f} pipdan kam o'zgardi, yangisini yubormaymiz.")
            return

    # 6. --> Shart-3: Probability < 70% yoki HOLD bo'lsa, yubormaslik
    if predicted_signal == 'HOLD' or probability < 0.7:
        print(f"Signal: {predicted_signal}, Aniqlik: {probability*100:.1f}% - Yuborilmadi.")
        return

    # 7. Yangi signal raqami
    signal_number = get_last_signal_number() + 1
    if signal_exists(signal_number):
        print(f"Signal #{signal_number} avval yuborilgan!")
        return

    # 8. TP/SL
    tp_price, sl_price = predict_tp_sl(latest_row, predicted_signal)

    # 9. Telegram xabari
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = (
        f"📊 Valyuta juftligi: GBP/USD (H1)\n"
        f"🕒 Vaqt: {current_time}\n"
        f"📍 Joriy narx: {current_price:.5f}\n"
        f"📌 Signal: {predicted_signal}\n"
        f"🎯 Take Profit (TP): {tp_price:.5f}\n"
        f"🛡 Stop Loss (SL): {sl_price:.5f}\n"
        f"📈 AI aniqligi: {min(probability*100, 95.0):.1f}%\n"
        f"🔢 Signal raqami: #{signal_number}"
    )

    bot.send_message(chat_id=CHAT_ID, text=message)
    print("[AI BOT] Signal yuborildi ->", message)

    # 10. MongoDB ga yozish
    signal_data = {
        "signal_number": signal_number,
        "currency_pair": "GBP/USD",
        "interval": "H1",
        "timestamp": current_time,
        "entry_price": current_price,
        "type": predicted_signal,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "accuracy": probability,
        "status": "active"
    }
    insert_signal(signal_data)
    print(f"[AI BOT] Signal #{signal_number} bazaga saqlandi (active).")

if __name__ == "__main__":
    # Har 10 daqiqada ishga tushirish
    while True:
        main()
        time.sleep(600)  # 10 minut