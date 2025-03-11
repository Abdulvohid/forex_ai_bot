from data_fetcher import fetch_forex_data
from indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_stochastic,
    calculate_adx,
    calculate_atr  # Yangilik: ATR funksiyasi
)

# GBP/USD narx ma'lumotlarini yuklash
df = fetch_forex_data(symbol="GBP/USD", interval="1h", outputsize=5000)

# Indikatorlarni hisoblash
df['EMA_14'] = calculate_ema(df, period=14)
df['RSI_14'] = calculate_rsi(df, period=14)
df['MACD'], df['MACD_signal'], df['MACD_histogram'] = calculate_macd(df)

df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df)
df['Stoch_%K'], df['Stoch_%D'] = calculate_stochastic(df)
df['ADX'] = calculate_adx(df)

# Yangi: ATR hisoblash
df['ATR'] = calculate_atr(df, period=14)

# Hisoblangan indikatorlarni ko‘rib chiqish
print(df.tail(10))
print(f"Ma'lumotlar soni: {len(df)} ta qator")
