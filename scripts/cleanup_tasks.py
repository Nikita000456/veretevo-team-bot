#!/usr/bin/env python3
"""
Скрипт для очистки завершенных и отмененных задач.
Можно запускать вручную или через cron для автоматической очистки.
"""

import sys
import os
import logging
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_veretevo.task_service import cleanup_finished_tasks

def main():
    """Основная функция очистки задач"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/home/ubuntu/bots/VeretevoTeam/logs/cleanup_tasks.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Начинаем очистку завершенных задач...")
        
        # Выполняем очистку
        removed_count = cleanup_finished_tasks()
        
        if removed_count > 0:
            logger.info(f"Очистка завершена успешно. Удалено задач: {removed_count}")
        else:
            logger.info("Очистка завершена. Завершенных задач для удаления не найдено.")
            
    except Exception as e:
        logger.error(f"Ошибка при очистке задач: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 