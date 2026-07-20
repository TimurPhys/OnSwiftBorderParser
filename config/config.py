import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# --- КОНСТАНТЫ ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

PAYMENT_SUBSCRIPTION_LINK = os.getenv("PAYMENT_SUBSCRIPTION_LINK")
PAYMENT_SUBSCRIPTION_AND_CALLS_LINK = os.getenv("PAYMENT_SUBSCRIPTION_AND_CALLS_LINK")
PAYMENT_CALLS_LINK = os.getenv("PAYMENT_CALLS_LINK")

VONAGE_APP_ID = os.getenv("VONAGE_APP_ID")
VONAGE_PRIVATE_KEY = os.getenv("VONAGE_PRIVATE_KEY")
VONAGE_VIRTUAL_NUMBER = os.getenv("VONAGE_VIRTUAL_NUMBER")

DB_NAME = os.getenv("DB_NAME")

border_names = {1: "Нарва", 2: "Койдула", 3: "Лухамаа"}
trans = {"morning": "Утро", "day": "День", "night": "Вечер/ночь", "any": "Любое"}
# --- КОНСТАНТЫ ----

# Глобальные переменные
monitoring_task = None
monitoring_counter = 0
first_monitoring_date = None
last_monitoring_date = None

# Словарь с персональными настройками пользователей
USER_FILTERS = {}
