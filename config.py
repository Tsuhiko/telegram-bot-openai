import os
from dotenv import load_dotenv

# Завантаження змінних з файлу .env
load_dotenv()

# Встановлення значень з файлу .env
session_name_bot = os.getenv('SESSION_NAME_BOT')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
model_engine = os.getenv('MODEL_ENGINE')
openai_key = os.getenv('OPENAI_KEY')

# Додання отриманих даних з .env для MySQL
MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
