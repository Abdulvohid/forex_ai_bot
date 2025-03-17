# FILE: src/trade/position_manager.py

import time
import math
from datetime import datetime
import MetaTrader5 as mt5
from dotenv import load_dotenv
import os

# trade_manager.py da yozib chiqqan funksiyalar:
from src.trade.trade_manager import modify_order_sl_tp, close_position

load_dotenv()

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "")

def initialize_mt5():
    """MetaTrader5 ga ulanadi."""
    if not mt5.initialize(path=MT5_PATH):
        print("[MT5] initialize xato:", mt5.last_error())
        return False

    authorized = mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("[MT5] login xato:", mt5.last_error())
        mt5.shutdown()
        return False

    acc_info = mt5.account_info()
    if acc_info:
        print("[MT5] Ulanish OK. Balans:", acc_info.balance)
    return True

def run_position_manager():
    """
    Ochilgan pozitsiyalarni tekshiradi.
    Agar foyda X pipsdan oshsa => trailing stopni surish (yoki partial close).
    """
    positions = mt5.positions_get()
    if not positions:
        print("[PM] Ochiq pozitsiya yo'q.")
        return

    for pos in positions:
        ticket = pos.ticket
        symbol = pos.symbol
        position_type = pos.type  # 0 = BUY, 1 = SELL
        open_price = pos.price_open
        volume = pos.volume

        # Joriy narxni olish
        tick_info = mt5.symbol_info_tick(symbol)
        if not tick_info:
            print(f"[PM] {symbol} symbol_info_tick topilmadi.")
            continue

        current_bid = tick_info.bid
        current_ask = tick_info.ask
        current_price = current_ask if position_type == mt5.POSITION_TYPE_BUY else current_bid

        # Masalan, trailing stop misoli: Agar +30 pip foyda bo'lsa, SL ni break-evenga suramiz
        # Pip hisobi brokerga bog'liq, shunchaki soddalashtiramiz.
        # Forex misol: 1 pip = 0.0001, goldda boshqacha bo'ladi
        profit_pips = (current_price - open_price) / 0.0001 if position_type == 0 else (open_price - current_price) / 0.0001

        # "break-even" narx:
        # BUY bo'lsa => SL = open_price, SELL bo'lsa => SL = open_price
        # 30 pip foyda bo'lsa, trailing stop ishga tushadi.
        if profit_pips > 30:
            # break-even SL ga surish
            if position_type == mt5.POSITION_TYPE_BUY:
                new_sl = open_price
            else:
                new_sl = open_price

            modify_order_sl_tp(order_ticket=ticket, new_sl=new_sl)
            print(f"[PM] Ticket#{ticket} => trailing stop ishga tushdi, SL={new_sl}")

        # Partial close misoli: Agar profit 50 pipsdan oshsa, 50% ni yopish
        if profit_pips > 50 and volume > 0.02:
            partial_lot = volume / 2  # Yarmini yopamiz
            close_position(order_ticket=ticket, lot=partial_lot)
            print(f"[PM] Ticket#{ticket} => partial close {partial_lot} lot")

def main_loop():
    if not initialize_mt5():
        return

    while True:
        run_position_manager()
        time.sleep(60)  # har 1 daqiqada tekshiramiz

    mt5.shutdown()

if __name__ == "__main__":
    main_loop()
