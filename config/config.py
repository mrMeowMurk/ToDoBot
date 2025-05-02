from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///todo_bot.db") 