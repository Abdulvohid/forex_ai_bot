import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from lightgbm import LGBMClassifier
from strategy import generate_trade_signals
from main import df
import joblib  # yangi qo'shildi

# AI uchun ma'lumot tayyorlash
df = generate_trade_signals(df)

# Indikatorlarni tanlash
features = [
    'EMA_14', 'RSI_14', 'MACD_histogram', 
    'BB_upper', 'BB_middle', 'BB_lower', 
    'Stoch_%K', 'Stoch_%D', 'ADX'
]

# HOLD signallarni olib tashlash (faqat BUY/SELL)
df_filtered = df[df['Signal'] != 'HOLD'].copy()

X = df_filtered[features]
y = df_filtered['Signal']

# Train va Testga bo'lish (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# LightGBM modelini yaratish va optimallashtirilgan parametrlarda o'qitish
model = LGBMClassifier(
    n_estimators=1000,
    learning_rate=0.01,
    max_depth=8,
    num_leaves=32,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# Bashorat qilish
y_pred = model.predict(X_test)

# Natijalarni baholash
accuracy = accuracy_score(y_test, y_pred)
print(f"Model aniqligi: {accuracy * 100:.2f}%")
print(classification_report(y_test, y_pred))

# Cross-validation orqali tekshirish
scores = cross_val_score(model, X, y, cv=5)
print(f"Cross-validation aniqligi: {scores.mean()*100:.2f}% (+/- {scores.std()*100:.2f}%)")

# Modelni faylga saqlash (yangi qo'shilgan qism)
joblib.dump(model, 'signal_model.pkl')
print("signal_model.pkl fayli muvaffaqiyatli yaratildi.")