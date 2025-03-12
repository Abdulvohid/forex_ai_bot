from src.utils.mongodb_connector import insert_signal

signal_data = {
    "signal_number": 99,
    "type": "BUY",
    "status": "active",
    "tp_price": 1.2970,   # <--- keraksiz bo'lsa ham xato chiqmasligi uchun kiritish
    "sl_price": 1.2920,   # <--- shuningdek
    "entry_price": 1.2940,
    "timestamp": "2025-03-12 12:00:00"
}

insert_signal(signal_data)
print("Signal #99 bazaga qo‘shildi!")