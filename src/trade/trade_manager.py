# FILE: src/trade/trade_manager.py

import MetaTrader5 as mt5
import math
from datetime import datetime

def calculate_lot_size(balance, risk_percent, stop_loss_pips, symbol="GBPUSD"):
    """
    Soddalashtirilgan lot hisobi - agar kerak bo'lsa.
    """
    risk_amount = balance * (risk_percent / 100.0)
    contract_size = 100000
    pip_value = 0.0001 * contract_size
    if "XAU" in symbol:
        contract_size = 100
        pip_value = 0.01 * contract_size

    if stop_loss_pips <= 0:
        stop_loss_pips = 10

    lot = risk_amount / (stop_loss_pips * pip_value)
    return round(lot, 2)

def place_order(symbol, order_type, lot, entry_price=None, sl_price=None, tp_price=None, comment="AI Robot Order"):
    """
    order_type: 'BUY' yoki 'SELL'
    return: butun 'result' obyekt (mt5.OrderSendResult), rad bo'lsa None
    """
    if order_type == "BUY":
        order_type_mt5 = mt5.ORDER_TYPE_BUY
    elif order_type == "SELL":
        order_type_mt5 = mt5.ORDER_TYPE_SELL
    else:
        print(f"[place_order] Noma'lum order_type: {order_type}")
        return None

    symbol_info = mt5.symbol_info_tick(symbol)
    if not symbol_info:
        print(f"[place_order] {symbol} => symbol_info_tick topilmadi!")
        return None

    if entry_price is None:
        entry_price = symbol_info.ask if order_type_mt5 == mt5.ORDER_TYPE_BUY else symbol_info.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type_mt5,
        "price": entry_price,
        "deviation": 10,
        "magic": 123456,
        "comment": comment
    }
    if sl_price is not None:
        request["sl"] = sl_price
    if tp_price is not None:
        request["tp"] = tp_price

    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[place_order] Xato! retcode={getattr(result,'retcode','None')}, comment={getattr(result,'comment','NoComment')}")
        return None

    print(f"[place_order] Muvaffaqiyatli! ORDER => {order_type}, lot={lot}, {symbol}@{entry_price}, SL={sl_price}, TP={tp_price}")
    return result  # butun obyekt

def modify_order_sl_tp(order_ticket, new_sl=None, new_tp=None):
    if not order_ticket:
        return None
    position_info = mt5.positions_get(ticket=order_ticket)
    if not position_info:
        print(f"[modify_order_sl_tp] Ticket#{order_ticket} topilmadi!")
        return None
    pos = position_info[0]
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": pos.ticket,
        "symbol": pos.symbol,
        "sl": new_sl if new_sl else pos.sl,
        "tp": new_tp if new_tp else pos.tp
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[modify_order_sl_tp] Xato! retcode={result.retcode}, comment={result.comment}")
        return None
    print(f"[modify_order_sl_tp] Ticket#{order_ticket} => SL={new_sl}, TP={new_tp}")
    return result

def close_position(order_ticket, lot=None):
    position_info = mt5.positions_get(ticket=order_ticket)
    if not position_info:
        print(f"[close_position] Ticket#{order_ticket} topilmadi!")
        return None

    pos = position_info[0]
    symbol = pos.symbol
    current_lot = pos.volume
    close_lot = lot if lot else current_lot
    close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"[close_position] {symbol} => symbol_info_tick xato!")
        return None
    price = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": close_lot,
        "type": close_type,
        "position": pos.ticket,
        "price": price,
        "deviation": 10,
        "magic": 123456,
        "comment": f"Close partial {close_lot} from {current_lot}"
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[close_position] Xato! retcode={result.retcode}, comment={result.comment}")
        return None

    print(f"[close_position] Ticket#{order_ticket} => {close_lot} lot yopildi")
    return result