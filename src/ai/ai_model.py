import os
import joblib
import numpy as np

# AI modeli uchun ishlatiladigan ustunlar
features_signal = [
    'EMA_14', 'RSI_14', 'MACD_histogram',
    'BB_upper', 'BB_middle', 'BB_lower',
    'Stoch_%K', 'Stoch_%D', 'ADX'
]

# 1) Loyihaning asosiy papkasini topamiz (BASE_DIR)
# __file__ -> "C:/path/to/forex_ai_bot/src/ai/ai_model.py"
# 2 marta yuqoriga chiqilsa -> "C:/path/to/forex_ai_bot"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# 2) signal_model.pkl ni 'data' papkadan yuklash
signal_model_path = os.path.join(BASE_DIR, 'data', 'signal_model.pkl')
signal_model = joblib.load(signal_model_path)

def predict_signal(row):
    X = row[features_signal].values.reshape(1, -1)
    proba = signal_model.predict_proba(X)[0]
    class_index = np.argmax(proba)
    signal = signal_model.classes_[class_index]
    probability = proba[class_index]
    return signal, probability

if __name__ == "__main__":
    # Bu faylni test qilish uchun
    print("AI model yuklandi:", signal_model_path)
    print("predict_signal funksiyasi ishga tayyor.")