import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


PAYMENT_SUBSCRIPTION_LINK = os.getenv("PAYMENT_SUBSCRIPTION_LINK")
PAYMENT_SUBSCRIPTION_AND_CALLS_LINK = os.getenv("PAYMENT_SUBSCRIPTION_AND_CALLS_LINK")

VONAGE_APP_ID = os.getenv("VONAGE_APP_ID")
VONAGE_PRIVATE_KEY = os.getenv("VONAGE_PRIVATE_KEY")
VONAGE_VIRTUAL_NUMBER = os.getenv("VONAGE_VIRTUAL_NUMBER")

DB_NAME = os.getenv("DB_NAME")

USER_FILTERS = {}
