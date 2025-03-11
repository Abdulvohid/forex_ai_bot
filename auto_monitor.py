import schedule
import time
import subprocess

def run_monitor():
    subprocess.run(["python", "signal_monitor.py"])

schedule.every(5).minutes.do(run_monitor)  # har 5 daqiqada tekshiradi

print("Signal monitor ishlamoqda...")

while True:
    schedule.run_pending()
    time.sleep(1)