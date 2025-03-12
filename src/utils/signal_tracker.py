import json
import os
from datetime import datetime

SIGNALS_FILE = 'signals.json'

# Signalni faylga saqlash
def save_signal(signal_number, entry_price, tp, sl, status='active'):
    signals = load_signals()

    signals[signal_number] = {
        'entry_price': entry_price,
        'tp': tp,
        'sl': sl,
        'status': status,
        'open_time': str(datetime.now())
    }

    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=4)

# Signal holatini yangilash
def update_signal_status(signal_number, status):
    signals = load_signals()

    if signal_number in signals:
        signals[signal_number]['status'] = status
        signals[signal_number]['close_time'] = str(datetime.now())

    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=4)

# Signallarni yuklash
def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return {}

    with open(SIGNALS_FILE, 'r') as f:
        return json.load(f)

# Faol signallarni olish
def get_active_signals():
    signals = load_signals()
    return {num: details for num, details in signals.items() if details['status'] == 'active'}