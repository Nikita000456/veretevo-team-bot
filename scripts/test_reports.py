#!/usr/bin/env python3
"""
Скрипт для тестирования отчетов
Использование:
    python3 scripts/test_reports.py morning  # Тест утреннего отчета
    python3 scripts/test_reports.py evening  # Тест вечернего отчета
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from telegram.ext import ApplicationBuilder
from config_veretevo.env import TELEGRAM_TOKEN
from handlers_veretevo.reports import send_morning_report, send_evening_report
from services_veretevo.department_service import load_departments
from services_veretevo.task_service import load_tasks

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def test_report(report_type):
    """Тестирование отчета"""
    print(f"🧪 Тестирование {report_type} отчета...")
    
    # Настройка логирования
    setup_logging()
    
    # Загружаем данные
    print("📂 Загрузка данных...")
    load_departments()
    load_tasks()
    
    # Создаем application
    print("🤖 Инициализация бота...")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    try:
        if report_type == "morning":
            print("🌅 Отправка утреннего отчета...")
            await send_morning_report(application.bot)
            print("✅ Утренний отчет отправлен успешно!")
            
        elif report_type == "evening":
            print("🌆 Отправка вечернего отчета...")
            await send_evening_report(application.bot)
            print("✅ Вечерний отчет отправлен успешно!")
            
        else:
            print("❌ Неизвестный тип отчета. Используйте 'morning' или 'evening'")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке отчета: {e}")
        logging.error(f"Ошибка при отправке отчета: {e}", exc_info=True)
        return False
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Использование:")
        print("  python3 scripts/test_reports.py morning  # Тест утреннего отчета")
        print("  python3 scripts/test_reports.py evening  # Тест вечернего отчета")
        sys.exit(1)
    
    report_type = sys.argv[1].lower()
    
    if report_type not in ["morning", "evening"]:
        print("❌ Неизвестный тип отчета. Используйте 'morning' или 'evening'")
        sys.exit(1)
    
    # Запускаем тест
    success = asyncio.run(test_report(report_type))
    
    if success:
        print("🎉 Тест завершен успешно!")
        sys.exit(0)
    else:
        print("💥 Тест завершен с ошибками!")
        sys.exit(1)

if __name__ == "__main__":
    main() 