#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт синхронизации баз контактов между основным ботом и AI ассистентом
"""

import json
import os
import shutil
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sync_contacts_databases():
    """Синхронизация баз контактов"""
    try:
        # Пути к базам данных
        main_bot_db = "data/suppliers_database.json"
        ai_assistant_db = "../shared/data/suppliers_database.json"
        
        logger.info("🔄 Начинаю синхронизацию баз контактов...")
        
        # Проверяем существование файлов
        if not os.path.exists(ai_assistant_db):
            logger.error(f"❌ База AI ассистента не найдена: {ai_assistant_db}")
            return False
        
        if not os.path.exists(main_bot_db):
            logger.info(f"📁 База основного бота не найдена, создаю новую: {main_bot_db}")
        
        # Читаем базу AI ассистента
        try:
            with open(ai_assistant_db, 'r', encoding='utf-8') as f:
                ai_data = json.load(f)
            logger.info(f"📖 Загружена база AI ассистента: {len(ai_data)} контактов")
        except Exception as e:
            logger.error(f"❌ Ошибка чтения базы AI ассистента: {e}")
            return False
        
        # Читаем базу основного бота (если существует)
        main_data = {}
        if os.path.exists(main_bot_db):
            try:
                with open(main_bot_db, 'r', encoding='utf-8') as f:
                    main_data = json.load(f)
                logger.info(f"📖 Загружена база основного бота: {len(main_data)} контактов")
            except Exception as e:
                logger.error(f"❌ Ошибка чтения базы основного бота: {e}")
                main_data = {}
        
        # Объединяем данные
        merged_data = {}
        updated_count = 0
        new_count = 0
        
        # Сначала добавляем все контакты из AI ассистента
        for phone, contact in ai_data.items():
            merged_data[phone] = contact.copy()
            if phone not in main_data:
                new_count += 1
            else:
                updated_count += 1
        
        # Добавляем контакты из основного бота, которых нет в AI ассистенте
        for phone, contact in main_data.items():
            if phone not in merged_data:
                merged_data[phone] = contact.copy()
                new_count += 1
        
        # Сохраняем объединенную базу в основной бот
        try:
            with open(main_bot_db, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Сохранена объединенная база в основной бот: {len(merged_data)} контактов")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в основной бот: {e}")
            return False
        
        # Создаем резервную копию AI ассистента
        backup_path = f"{ai_assistant_db}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copy2(ai_assistant_db, backup_path)
            logger.info(f"💾 Создана резервная копия AI ассистента: {backup_path}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось создать резервную копию: {e}")
        
        # Обновляем базу AI ассистента
        try:
            with open(ai_assistant_db, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Обновлена база AI ассистента: {len(merged_data)} контактов")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления AI ассистента: {e}")
            return False
        
        # Создаем отчет
        report = f"""
📊 ОТЧЕТ СИНХРОНИЗАЦИИ КОНТАКТОВ
{'='*50}
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📱 Всего контактов: {len(merged_data)}
🔄 Обновлено: {updated_count}
➕ Добавлено новых: {new_count}
📁 Основной бот: {main_bot_db}
🤖 AI ассистент: {ai_assistant_db}
💾 Резервная копия: {backup_path}
✅ Синхронизация завершена успешно!
"""
        
        logger.info(report)
        print(report)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка синхронизации: {e}")
        return False

def create_sync_script():
    """Создание bash скрипта для автоматической синхронизации"""
    script_content = '''#!/bin/bash
# Скрипт автоматической синхронизации контактов
cd "$(dirname "$0")"
python3 sync_contacts.py
'''
    
    script_path = "sync_contacts.sh"
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        logger.info(f"📝 Создан bash скрипт: {script_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания bash скрипта: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Запуск синхронизации баз контактов")
    
    # Синхронизируем базы
    if sync_contacts_databases():
        # Создаем bash скрипт для удобства
        create_sync_script()
        logger.info("🎉 Синхронизация завершена успешно!")
    else:
        logger.error("❌ Синхронизация завершена с ошибками!")
        exit(1)
