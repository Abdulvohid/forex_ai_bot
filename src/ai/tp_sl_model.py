import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import numpy as np

# Optimal TP/SL ma'lumotlari
df = pd.read_csv('optimal_trades.csv')

# Feature va targetlarni belgilash
X = df[['EMA_14', 'RSI_14', 'MACD_histogram', 'BB_middle', 'ADX', 'ATR']]
y_tp = df['optimal_TP']
y_sl = df['optimal_SL']

# Train va testga ajratish
X_train_tp, X_test_tp, y_train_tp, y_test_tp = train_test_split(X, y_tp, test_size=0.2, random_state=42)
X_train_sl, X_test_sl, y_train_sl, y_test_sl = train_test_split(X, y_sl, test_size=0.2, random_state=42)

# TP uchun model yaratish
tp_model = LGBMRegressor(n_estimators=100)
tp_model.fit(X_train_tp, y_train_tp)

# SL uchun model yaratish
sl_model = LGBMRegressor(n_estimators=100)
sl_model.fit(X_train_sl, y_train_sl)

# Modelni baholash
y_tp_pred = tp_model.predict(X_test_tp)
y_sl_pred = sl_model.predict(X_test_sl)

tp_rmse = np.sqrt(mean_squared_error(y_test_tp, y_tp_pred))
sl_rmse = np.sqrt(mean_squared_error(y_test_sl, y_sl_pred))

print(f'TP RMSE: {tp_rmse:.5f}')
print(f'SL RMSE: {sl_rmse:.5f}')

# Modelni saqlash
joblib.dump(tp_model, 'tp_model.pkl')
joblib.dump(sl_model, 'sl_model.pkl')