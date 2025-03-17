import os
from dotenv import load_dotenv

load_dotenv()
print("MT5_PATH:", os.getenv("MT5_PATH"))