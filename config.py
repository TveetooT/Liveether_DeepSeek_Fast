import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    ROOT_CODE = os.getenv("ROOT_CODE")
    PORT = int(os.getenv("PORT", 5000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    if not all([TELEGRAM_TOKEN, SUPABASE_URL, SUPABASE_KEY, WEBHOOK_URL, ROOT_CODE]):
        raise ValueError("Не все переменные окружения заданы")