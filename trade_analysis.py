import pandas as pd
from strategy import generate_trade_signals
from main import df  # main.py dan indikatorlar hisoblangan DataFrame

# ATRga asoslangan dinamik TP/SL koeffitsientlari
TP_multiple = 1/2
SL_multiple = 1/1

def trade_analysis(df):
    """
    Dinamik TP/SL (ATR ga asoslangan) bo'yicha har bir savdo bitimini tahlil qiladi.
    Natijada TP, SL yoki No Result (vaqt tugaguncha neither) bo'lishi mumkin.
    """
    # Strategiya signallarini DataFrame ga qo'shish
    df = generate_trade_signals(df)

    trades = []

    for i in range(len(df) - 1):
        signal = df.iloc[i]['Signal']
        entry_price = df.iloc[i]['close']
        atr_value = df.iloc[i]['ATR']  # Shu paytdagi ATR qiymati

        # ATR qiymati NaN bo'lganda o‘tkazib yuboramiz
        if pd.isna(atr_value):
            continue

        tp_distance = atr_value * TP_multiple
        sl_distance = atr_value * SL_multiple

        if signal == 'BUY':
            tp_price = entry_price + tp_distance
            sl_price = entry_price - sl_distance

            result = 'No Result'
            for j in range(i+1, len(df)):
                high_price = df.iloc[j]['high']
                low_price = df.iloc[j]['low']

                # TP urilishi
                if high_price >= tp_price:
                    result = 'TP'
                    break
                # SL urilishi
                elif low_price <= sl_price:
                    result = 'SL'
                    break

            trades.append({
                'Type': 'BUY',
                'Entry': entry_price,
                'ATR': atr_value,
                'Result': result
            })

        elif signal == 'SELL':
            tp_price = entry_price - tp_distance
            sl_price = entry_price + sl_distance

            result = 'No Result'
            for j in range(i+1, len(df)):
                high_price = df.iloc[j]['high']
                low_price = df.iloc[j]['low']

                # TP urilishi
                if low_price <= tp_price:
                    result = 'TP'
                    break
                # SL urilishi
                elif high_price >= sl_price:
                    result = 'SL'
                    break

            trades.append({
                'Type': 'SELL',
                'Entry': entry_price,
                'ATR': atr_value,
                'Result': result
            })

    results_df = pd.DataFrame(trades)
    return results_df

if __name__ == "__main__":
    # Dinamik TP/SL tahlilini ishga tushiramiz
    results = trade_analysis(df)

    # Qancha TP, SL, No Result bo'lganini ko'rish
    print(results['Result'].value_counts())

    # Dastlabki 20 ta bitimni ko'rish
    print(results.head(20))