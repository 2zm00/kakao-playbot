import os
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
BOT_NAME    = os.getenv("BOT_NAME")
DELAY       = os.getenv("DELAY")
WAIT_REPLY  = os.getenv("WAIT_REPLY")
TARGET_ENFORCE = os.getenv("TARGET_ENFORCE")
MY_USER_NAME = os.getenv("MY_USER_NAME")