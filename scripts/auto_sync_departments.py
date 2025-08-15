#!/usr/bin/env python3
"""
Автоматическая синхронизация отделов с Telegram-группами.
Предназначен для запуска по расписанию (cron) для поддержания актуальности конфигурации.
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils_veretevo.telegram_sync import TelegramGroupSync
from services_veretevo.department_service import load_departments, DEPARTMENTS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/department_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def auto_sync_departments():
    """Автоматическая синхронизация всех отделов"""
    start_time = datetime.now()
    logger.info(f"🚀 Начало автоматической синхронизации отделов: {start_time}")
    
    try:
        sync = TelegramGroupSync()
        results = await sync.sync_all_departments()
        
        # Подсчитываем статистику
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"📊 Результаты синхронизации: {successful}/{total} отделов успешно")
        
        # Логируем детали
        for department, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {department}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"⏱️ Синхронизация завершена за {duration:.2f} секунд")
        
        return successful == total
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка синхронизации: {e}")
        return False

async def sync_with_backup():
    """Синхронизация с созданием резервной копии"""
    from services_veretevo.department_service import save_departments
    
    # Создаем резервную копию
    backup_path = f"config_veretevo/departments_config.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        load_departments()
        
        # Сохраняем текущую конфигурацию
        import json
        with open("config_veretevo/departments_config.json", 'r', encoding='utf-8') as f:
            current_config = json.load(f)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Создана резервная копия: {backup_path}")
        
        # Выполняем синхронизацию
        success = await auto_sync_departments()
        
        if success:
            logger.info("✅ Синхронизация прошла успешно")
            # Удаляем резервную копию если все прошло хорошо
            try:
                os.remove(backup_path)
                logger.info("🗑️ Резервная копия удалена")
            except:
                pass
        else:
            logger.warning("⚠️ Синхронизация прошла с ошибками, резервная копия сохранена")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании резервной копии: {e}")
        return False

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Автоматическая синхронизация отделов")
    parser.add_argument("--backup", action="store_true", 
                       help="Создать резервную копию перед синхронизацией")
    parser.add_argument("--dry-run", action="store_true",
                       help="Показать различия без синхронизации")
    
    args = parser.parse_args()
    
    if args.dry_run:
        # Показываем различия без синхронизации
        asyncio.run(show_differences_only())
    elif args.backup:
        # Синхронизация с резервной копией
        success = asyncio.run(sync_with_backup())
        sys.exit(0 if success else 1)
    else:
        # Обычная синхронизация
        success = asyncio.run(auto_sync_departments())
        sys.exit(0 if success else 1)

async def show_differences_only():
    """Показывает различия без синхронизации"""
    logger.info("🔍 Анализ различий в отделах...")
    
    try:
        sync = TelegramGroupSync()
        load_departments()
        
        total_differences = 0
        
        for department_key in DEPARTMENTS.keys():
            if DEPARTMENTS[department_key].get("chat_id"):
                diff = await sync.get_department_diff(department_key)
                
                if "error" not in diff:
                    missing = len(diff["missing_in_config"])
                    extra = len(diff["extra_in_config"])
                    
                    if missing > 0 or extra > 0:
                        total_differences += missing + extra
                        logger.info(f"📊 {department_key}: +{missing} -{extra} различий")
                    else:
                        logger.info(f"✅ {department_key}: актуально")
        
        if total_differences == 0:
            logger.info("🎉 Все отделы актуальны!")
        else:
            logger.info(f"📋 Всего различий: {total_differences}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка анализа: {e}")

if __name__ == "__main__":
    main() 