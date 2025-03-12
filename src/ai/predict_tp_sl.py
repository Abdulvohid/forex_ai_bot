import joblib
import numpy as np
import os

# Faylni 'data' papkasidan to'g'ri yuklash
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
tp_model_path = os.path.join(BASE_DIR, 'data', 'tp_model.pkl')
sl_model_path = os.path.join(BASE_DIR, 'data', 'sl_model.pkl')

tp_model = joblib.load(tp_model_path)
sl_model = joblib.load(sl_model_path)

features_tp_sl = ['EMA_14', 'RSI_14', 'MACD_histogram', 'BB_middle', 'ADX', 'ATR']

def predict_tp_sl(row, predicted_signal):
    X = row[features_tp_sl].values.reshape(1, -1)
    tp_pred = tp_model.predict(X)[0]
    sl_pred = sl_model.predict(X)[0]

    current_price = row['close']
    if predicted_signal == 'BUY':
        tp_price = current_price + tp_pred
        sl_price = current_price - sl_pred
    else:
        tp_price = current_price - tp_pred
        sl_price = current_price + sl_pred

    tp_price = round(tp_price, 5)
    sl_price = round(sl_price, 5)
    return tp_price, sl_price

if __name__ == "__main__":
    print("predict_tp_sl import test: OK")