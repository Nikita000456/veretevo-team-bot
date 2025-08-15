#!/usr/bin/env python3
"""
Скрипт для отправки тестовых сообщений во все активные группы
"""
import json
import requests
import time
from datetime import datetime
import pytz

# Загружаем конфигурацию
with open('config_veretevo/departments_config.json', 'r', encoding='utf-8') as f:
    DEPARTMENTS = json.load(f)

# Загружаем токен из переменных окружения
import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN не найден в переменных окружения")
    exit(1)

def send_test_message(chat_id, department_name):
    """Отправляет тестовое сообщение в группу"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz).strftime("%d.%m %H:%M")
    
    message = f"""🧪 **ТЕСТОВОЕ СООБЩЕНИЕ**

📅 Дата: {current_time}
🏢 Группа: {department_name}
🤖 От: Veretevo Bot

✅ Бот работает корректно
🔊 Готов к обработке голосовых сообщений
📝 Готов к созданию задач

_Это автоматическое тестовое сообщение для проверки работоспособности бота_"""

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ {department_name}: сообщение отправлено")
                return True
            else:
                print(f"❌ {department_name}: ошибка API - {result.get('description', 'неизвестно')}")
                return False
        else:
            print(f"❌ {department_name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {department_name}: ошибка отправки - {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 === ОТПРАВКА ТЕСТОВЫХ СООБЩЕНИЙ ===\n")
    
    # Фильтруем только активные группы с chat_id
    active_groups = []
    for key, dept in DEPARTMENTS.items():
        if dept.get('chat_id'):
            active_groups.append((key, dept['name'], dept['chat_id']))
    
    print(f"📋 Найдено {len(active_groups)} активных групп:")
    for key, name, chat_id in active_groups:
        print(f"  • {name} ({key}): {chat_id}")
    
    print(f"\n📤 Отправка тестовых сообщений...")
    
    success_count = 0
    for key, name, chat_id in active_groups:
        if send_test_message(chat_id, name):
            success_count += 1
        time.sleep(1)  # Небольшая пауза между отправками
    
    print(f"\n📊 Результат: {success_count}/{len(active_groups)} сообщений отправлено успешно")
    
    if success_count == len(active_groups):
        print("🎉 Все тестовые сообщения отправлены успешно!")
    else:
        print("⚠️ Некоторые сообщения не удалось отправить")

if __name__ == "__main__":
    main()

