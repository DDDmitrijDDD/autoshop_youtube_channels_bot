import os
from dotenv import load_dotenv

load_dotenv()

# токен бота
BOT_TOKEN = str(os.getenv("TOKEN"))

API_KEY = str(os.getenv("API_KEY"))

SHOP_ID = str(os.getenv("SHOP_ID"))

# flood-time
rate = 1

# id админов
admins_id = [923162995, 8733693220]