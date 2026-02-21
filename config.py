import os
from dotenv import load_dotenv

load_dotenv()

# Bot token - @BotFather dan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Database - Railway PostgreSQL yoki SQLite (local test uchun)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///medbot.db")

# Klinika ma'lumotlari (har bir klinika uchun alohida sozlanadi)
CLINIC_NAME = os.getenv("CLINIC_NAME", "MedCenter")
CLINIC_ADDRESS = os.getenv("CLINIC_ADDRESS", "Toshkent, Yunusobod tumani, 5-mavze")
CLINIC_PHONE = os.getenv("CLINIC_PHONE", "+998 71 123 45 67")

# Admin Telegram ID lari (vergul bilan ajratilgan)
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",")]

# Ish vaqti sozlamalari
WORK_START = os.getenv("WORK_START", "09:00")
WORK_END = os.getenv("WORK_END", "18:00")
SLOT_DURATION = int(os.getenv("SLOT_DURATION", "30"))  # daqiqa
