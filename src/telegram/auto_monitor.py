import schedule
import time
import subprocess
import os

def run_monitor():
    # Windows muhiti uchun venv ichidagi Python'ni ishga tushirish
    python_exe = os.path.join('.', 'venv', 'Scripts', 'python.exe')
    subprocess.run([python_exe, "src/telegram/signal_monitor.py"])

# Har 5 daqiqada signal_monitor.py ni ishga tushiradi
schedule.every(5).minutes.do(run_monitor)

print("Signal monitor ishlamoqda...")

while True:
    schedule.run_pending()
    time.sleep(1)