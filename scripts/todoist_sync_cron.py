#!/usr/bin/env python3
"""
Скрипт для синхронизации с Todoist через cron
Запускается каждую минуту для проверки обновлений
"""

import sys
import os
import json
import logging
from datetime import datetime

# Добавляем путь к проекту в sys.path (скрипт находится в scripts/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
            logging.FileHandler('../logs/todoist_sync.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
)

def main():
    """Основная функция для синхронизации с Todoist"""
    try:
        # Импортируем необходимые модули
        from utils_veretevo.todoist_sync_polling import sync_todoist_to_bot
        from config_veretevo.constants import GENERAL_DIRECTOR_ID
        from config_veretevo.env import TELEGRAM_TOKEN
        
        # Используем боевой файл задач
        TASKS_FILE = "../data/tasks.json"
        
        # Загружаем существующие задачи
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            tasks = []
            logging.warning(f"Файл {TASKS_FILE} не найден или поврежден, создаем пустой список задач")
        
        logging.info(f"Запуск синхронизации с Todoist. Загружено {len(tasks)} задач")
        
        # Запускаем синхронизацию (без application, так как это отдельный процесс)
        sync_todoist_to_bot(tasks, GENERAL_DIRECTOR_ID, application=None)
        
        # Сохраняем обновленные задачи
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        logging.info("Синхронизация с Todoist завершена успешно")
        
    except Exception as e:
        logging.error(f"Ошибка при синхронизации с Todoist: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 