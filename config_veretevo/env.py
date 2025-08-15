import os
from dotenv import load_dotenv

load_dotenv()

# Боевые настройки (единственный режим)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ASSISTANTS_CHAT_ID_STR = os.getenv("ASSISTANTS_CHAT_ID")
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN не установлен в переменных окружения")
if ASSISTANTS_CHAT_ID_STR is None:
    raise ValueError("ASSISTANTS_CHAT_ID не установлен в переменных окружения")
ASSISTANTS_CHAT_ID = int(ASSISTANTS_CHAT_ID_STR)
FINANCE_CHAT_ID = int(os.getenv("FINANCE_CHAT_ID", "-1002844492561"))

# Yandex SpeechKit Configuration
YANDEX_SPEECHKIT_API_KEY = os.getenv("YANDEX_SPEECHKIT_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Yandex GPT Configuration
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # По умолчанию используем gpt-4o-mini

# Проверка обязательных переменных Yandex SpeechKit
if YANDEX_SPEECHKIT_API_KEY is None:
    print("[ПРЕДУПРЕЖДЕНИЕ] YANDEX_SPEECHKIT_API_KEY не установлен")
if YANDEX_FOLDER_ID is None:
    print("[ПРЕДУПРЕЖДЕНИЕ] YANDEX_FOLDER_ID не установлен")

# Проверка переменных Yandex GPT
if YANDEX_GPT_API_KEY is None:
    print("[ПРЕДУПРЕЖДЕНИЕ] YANDEX_GPT_API_KEY не установлен - GPT-подсказки будут недоступны")

# Проверка переменных OpenAI
if OPENAI_API_KEY is None:
    print("[ПРЕДУПРЕЖДЕНИЕ] OPENAI_API_KEY не установлен - OpenAI функции будут недоступны")

# Пример использования:
# Создайте файл .env со следующими переменными:
# TELEGRAM_TOKEN=ваш_токен
# ASSISTANTS_CHAT_ID=ваш_чат_id
# FINANCE_CHAT_ID=ваш_фин_чат_id
# YANDEX_SPEECHKIT_API_KEY=ваш_api_ключ_yandex_speechkit
# YANDEX_FOLDER_ID=ваш_folder_id_yandex_cloud
# YANDEX_GPT_API_KEY=ваш_api_ключ_yandex_gpt
# OPENAI_API_KEY=ваш_api_ключ_openai
# OPENAI_MODEL=gpt-4o-mini

def load_env():
    pass  # Заглушка для совместимости, если потребуется доинициализация
