#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки вечернего отчета
"""

import sys
import os
import asyncio
import logging

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_veretevo.env import TELEGRAM_TOKEN
from telegram import Bot
from handlers_veretevo.reports import send_evening_report
from services_veretevo.department_service import load_departments, DEPARTMENTS
import services_veretevo.task_service as task_service

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def test_evening_report():
    """Тестирует отправку вечернего отчета"""
    setup_logging()
    
    print("=== Тест вечернего отчета ===")
    
    # Загружаем отделы
    print("Загрузка отделов...")
    load_departments()
    
    # Проверяем отделы
    print(f"Загружено отделов: {len(DEPARTMENTS)}")
    for dep_key, dep in DEPARTMENTS.items():
        chat_id = dep.get("chat_id")
        print(f"  {dep['name']}: chat_id = {chat_id}")
    
    # Загружаем задачи
    print("Загрузка задач...")
    task_service.load_tasks()
    print(f"Загружено задач: {len(task_service.tasks)}")
    
    # Создаем бота
    bot = Bot(token=TELEGRAM_TOKEN)
    
    try:
        print("Отправка вечернего отчета...")
        await send_evening_report(bot)
        print("✅ Вечерний отчет отправлен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка отправки вечернего отчета: {e}")
        logging.error(f"Ошибка отправки вечернего отчета: {e}", exc_info=True)
    
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_evening_report()) 