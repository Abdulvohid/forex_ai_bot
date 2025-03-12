import MetaTrader5 as mt5

init_path = r"C:\Program Files\Gerchik & Co MetaTrader 5\terminal64.exe"  # misol!

print("MT5 ni ishga tushiramiz...")
if not mt5.initialize(path=init_path):
    print("initialize() xato:", mt5.last_error())
    mt5.shutdown()
    exit()

print("MT5 initialize muvaffaqiyatli!")

# Hozir terminal login window’ga “kapingizni” kiritishga harakat qiladi.
# Biroq siz allaqachon login bo'lgansiz, baribir broker "Authorization" jarayoni to'g'ri bo'lsa, qabul qiladi.

authorized = mt5.login(login=127346, password="k{6F$K8n", server="GerchikCo-MT5")
if not authorized:
    print("Login muvaffaqiyatsiz:", mt5.last_error())
    mt5.shutdown()
    exit()

print("MetaTrader5 ga muvaffaqiyatli ulanildi!")
account_info = mt5.account_info()
print("account_info =", account_info)

mt5.shutdown()