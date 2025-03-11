import pandas as pd
from main import df
from strategy import generate_trade_signals

def generate_optimal_tp_sl(df, lookahead=12):
    signals_df = generate_trade_signals(df)
    data = []

    for i in range(len(signals_df) - lookahead):
        row = signals_df.iloc[i]
        signal = row['Signal']
        entry_price = row['close']

        if signal == 'HOLD':
            continue

        future_data = signals_df.iloc[i+1:i+lookahead]

        if signal == 'BUY':
            high_max = future_data['high'].max()
            low_min = future_data['low'].min()

            optimal_tp = high_max - entry_price
            optimal_sl = entry_price - low_min

            data.append({
                'datetime': row['datetime'],
                'Type': 'BUY',
                'EMA_14': row['EMA_14'],
                'RSI_14': row['RSI_14'],
                'MACD_histogram': row['MACD_histogram'],
                'BB_middle': row['BB_middle'],
                'ADX': row['ADX'],
                'ATR': row['ATR'],
                'optimal_TP': optimal_tp,
                'optimal_SL': optimal_sl
            })

            print(f"[{row['datetime']}] BUY uchun TP: {optimal_tp:.5f}, SL: {optimal_sl:.5f}")

        elif signal == 'SELL':
            high_max = future_data['high'].max()
            low_min = future_data['low'].min()

            optimal_tp = entry_price - low_min
            optimal_sl = high_max - entry_price

            data.append({
                'datetime': row['datetime'],
                'Type': 'SELL',
                'EMA_14': row['EMA_14'],
                'RSI_14': row['RSI_14'],
                'MACD_histogram': row['MACD_histogram'],
                'BB_middle': row['BB_middle'],
                'ADX': row['ADX'],
                'optimal_TP': optimal_tp,
                'optimal_SL': optimal_sl
            })

            print(f"{row['datetime']} - {signal} signali uchun TP: {optimal_tp:.5f}, SL: {optimal_sl:.5f}")

    return pd.DataFrame(data)

# Funksiyani ishga tushirish
if __name__ == "__main__":
    optimal_trades = generate_optimal_tp_sl(df, lookahead=12)
    optimal_trades.dropna(inplace=True)

    print(optimal_trades.head(20))
    print(optimal_trades[['optimal_TP', 'optimal_SL']].describe())
optimal_trades.to_csv('optimal_trades.csv', index=False)
print("CSV fayl muvaffaqiyatli saqlandi!")