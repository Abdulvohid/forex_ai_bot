from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

bot = Bot(token=bot_token)

# Telegramga savdo signalini yuborish
def send_trade_signal(signal_type, entry_price, tp, sl):
    message = (
        f"📊 Yangi savdo signali:\n\n"
        f"🔹 Turi: {signal_type}\n"
        f"🔹 Narx: {entry_price}\n"
        f"🎯 Take Profit: {tp}\n"
        f"🛑 Stop Loss: {sl}"
    )

    bot.send_message(chat_id=chat_id, text=message)

# Test uchun xabar yuborish
if __name__ == "__main__":
    send_trade_signal('BUY', 1.2900, 1.2950, 1.2850)