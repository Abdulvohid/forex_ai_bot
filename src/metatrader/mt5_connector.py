import MetaTrader5 as mt5

def connect(account_number, password, server):
    if not mt5.initialize(login=account_number, password=password, server=server):
        print("MT5 ulanish xatosi:", mt5.last_error())
        return False
    else:
        print("✅ MT5 ga muvaffaqiyatli ulandi!")
        return True

def get_account_info():
    account_info = mt5.account_info()
    if account_info is None:
        print("Hisob ma'lumotlarini olishda xatolik:", mt5.last_error())
        return None
    else:
        print(f"Hisob raqami: {account_info.login}")
        print(f"Balans: {account_info.balance}")
        print(f"Equity: {account_info.equity}")
        return account_info

def disconnect():
    mt5.shutdown()
    print("🔴 MT5 bilan aloqa tugatildi.")