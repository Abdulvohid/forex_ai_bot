import os
import sys
from subprocess import Popen

# 1) "src" papkasini Python import yo'liga (sys.path) qo'shamiz,
#    shunda "from src.xyz" importlari "main.py" chaqilganda ham ishlaydi.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 2) Endi "src" papkasidagi modullarni import qilamiz.
from utils.data_fetcher import fetch_forex_data
from indicators.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_stochastic,
    calculate_adx,
    calculate_atr
)

# Windows muhiti uchun aniq venv python ni olish
# (Agar Mac/Linux bo'lsa, bu 'venv/bin/python' bo'lishi mumkin.)
venv_python = os.path.join('.', 'venv', 'Scripts', 'python.exe')

def main():
    # 1) GBP/USD narx ma'lumotlarini yuklash
    df = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=5000)

    # 2) Indikatorlarni hisoblash
    df['EMA_14'] = calculate_ema(df, period=14)
    df['RSI_14'] = calculate_rsi(df, period=14)
    df['MACD'], df['MACD_signal'], df['MACD_histogram'] = calculate_macd(df)
    df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df)
    df['Stoch_%K'], df['Stoch_%D'] = calculate_stochastic(df)
    df['ADX'] = calculate_adx(df)
    df['ATR'] = calculate_atr(df, period=14)

    # 3) Hisoblangan indikatorlarni terminalda ko‘rib chiqish
    print(df.tail(10))
    print(f"Ma'lumotlar soni: {len(df)} ta qator")

    # 4) Boshqa Telegram skriptlarni ishga tushirish
    #    "-m" bayrog‘i bilan paket sifatida ishga tushiriladi
    Popen([venv_python, "-m", "src.telegram.telegram_ai_bot"])
    Popen([venv_python, "-m", "src.telegram.signal_monitor"])
    Popen([venv_python, "-m", "src.telegram.auto_monitor"])

    print("Barcha skriptlar ishga tushirildi...")

if __name__ == "__main__":
    main()