import os

from dotenv import load_dotenv
from supabase import Client, create_client

REQUIRED_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]

if not os.path.exists(".env"):
    raise FileNotFoundError(".env file not found")

try:
    load_dotenv()
except Exception as e:
    raise RuntimeError(f"Error loading .env: {e}")

missing = [var for var in REQUIRED_VARS if not os.environ.get(var)]
if missing:
    raise ValueError("Missing environment variables: " + ", ".join(missing))

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID: str = os.environ["TELEGRAM_CHAT_ID"]

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to create Supabase client: {e}")
