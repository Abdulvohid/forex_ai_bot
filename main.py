import os
import sys
from subprocess import Popen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Windows muhiti uchun aniq venv python ni olish.
# Agar Mac/Linux bo'lsa, 'venv/bin/python' bo'lishi mumkin.
venv_python = os.path.join('.', 'venv', 'Scripts', 'python.exe')
if not os.path.exists(venv_python):
    venv_python = os.path.join('.', 'venv', 'bin', 'python')

def main():
    """
    1) live_demo_trading.py -> Robot
    2) trade_monitor.py -> TP/SL kuzatish
    3) daily_report.py -> Kunlik hisobot (bir martalik skript)
    """
    print("[main.py] Robot (live_demo_trading) ni ishga tushiramiz...")
    p1 = Popen([venv_python, "-m", "src.trade.live_demo_trading"])

    print("[main.py] Monitor (trade_monitor) ni ishga tushiramiz...")
    p2 = Popen([venv_python, "-m", "src.trade.trade_monitor"])

    print("[main.py] Daily report (daily_report) ni ishga tushiramiz...")
    p3 = Popen([venv_python, "-m", "src.trade.daily_report"])

    print("[main.py] Barcha jarayonlar ishga tushirildi. Terminal loglarini kuzating...")

    p1.wait()
    p2.wait()
    p3.wait()

if __name__ == "__main__":
    main()