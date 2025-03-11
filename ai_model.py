import joblib
import numpy as np

features_signal = [
    'EMA_14', 'RSI_14', 'MACD_histogram',
    'BB_upper', 'BB_middle', 'BB_lower',
    'Stoch_%K', 'Stoch_%D', 'ADX'
]

signal_model = joblib.load('signal_model.pkl')

def predict_signal(row):
    X = row[features_signal].values.reshape(1, -1)
    proba = signal_model.predict_proba(X)[0]
    class_index = np.argmax(proba)
    signal = signal_model.classes_[class_index]
    probability = proba[class_index]
    return signal, probability