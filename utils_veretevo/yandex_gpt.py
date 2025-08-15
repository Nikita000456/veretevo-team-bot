import os
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

YANDEX_GPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")

PROMPT = (
    "Исправь ошибки и улучши текст задачи, надиктованный голосом. "
    "Не меняй смысл, только исправь ошибки и сделай текст более понятным. "
    "Ответь только улучшенным текстом, без пояснений."
)

def improve_task_text(text: str) -> str:
    if not YANDEX_GPT_API_KEY:
        print(f"[WARN] YANDEX_GPT_API_KEY не задан в переменных окружения! Возвращаем исходный текст.")
        return text  # fallback: возвращаем исходный текст
    
    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "modelUri": "gpt://b1g8c7c7c7c7c7c7c7c7/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 200},
        "messages": [
            {"role": "system", "text": PROMPT},
            {"role": "user", "text": text}
        ]
    }
    try:
        resp = requests.post(YANDEX_GPT_API_URL, headers=headers, json=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        print(f"[ОШИБКА] YandexGPT: {e}")
        return text  # fallback: возвращаем исходный текст 