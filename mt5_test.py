from mt5_connector import connect, get_account_info, disconnect

# Sizning hisobingiz ma'lumotlari (demo hisob ishlatishni tavsiya qilamiz!)
ACCOUNT_NUMBER = 12345678      # Sizning hisob raqamingiz
PASSWORD = "password"          # Sizning hisob parolingiz
SERVER = "broker_server"       # Masalan: "Exness-MT5Trial"

# MT5 bilan ulanish
if connect(ACCOUNT_NUMBER, PASSWORD, SERVER):
    # Hisob haqida ma'lumot olish
    get_account_info()

    # Aloqani tugatish
    disconnect()