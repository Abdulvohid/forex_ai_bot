def generate_trade_signals(df):
    """
    Row by row yurib, eng oddiy shartlarga asoslanib 'Signal' ustuni yaratish.
    'BUY', 'SELL' yoki 'HOLD'
    """
    signals = []
    for i in range(len(df)):
        row = df.iloc[i]

        # Shart (sodda misol)
        buy_condition = (
            row['close'] > row['EMA_14'] and
            row['RSI_14'] > 50 and
            row['MACD_histogram'] > 0 and
            row['ADX'] > 20
        )
        sell_condition = (
            row['close'] < row['EMA_14'] and
            row['RSI_14'] < 50 and
            row['MACD_histogram'] < 0 and
            row['ADX'] > 20
        )

        if buy_condition:
            signals.append('BUY')
        elif sell_condition:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    df['Signal'] = signals
    return df