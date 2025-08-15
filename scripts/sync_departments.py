#!/usr/bin/env python3
"""
Скрипт для синхронизации членов Telegram-групп с конфигурацией отделов.
Позволяет автоматически обновлять список участников отделов.
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils_veretevo.telegram_sync import TelegramGroupSync
from services_veretevo.department_service import load_departments, DEPARTMENTS

def print_department_info():
    """Выводит информацию о текущих отделах"""
    load_departments()
    print("📋 Текущие отделы:")
    for key, dept in DEPARTMENTS.items():
        chat_id = dept.get("chat_id", "Не указан")
        members_count = len(dept.get("members", {}))
        print(f"  • {dept['name']} ({key}): {members_count} участников, chat_id: {chat_id}")

async def sync_specific_department(department_key: str):
    """Синхронизирует конкретный отдел"""
    try:
        sync = TelegramGroupSync()
        
        # Показываем различия перед синхронизацией
        print(f"🔍 Анализ отдела '{department_key}'...")
        diff = await sync.get_department_diff(department_key)
        
        if "error" in diff:
            print(f"❌ Ошибка: {diff['error'][0]}")
            return
        
        print(f"📊 Различия в отделе '{department_key}':")
        if diff["missing_in_config"]:
            print(f"  ➕ Отсутствуют в конфигурации: {diff['missing_in_config']}")
        if diff["extra_in_config"]:
            print(f"  ➖ Лишние в конфигурации: {diff['extra_in_config']}")
        if not diff["missing_in_config"] and not diff["extra_in_config"]:
            print("  ✅ Конфигурация актуальна")
        
        # Выполняем синхронизацию
        print(f"🔄 Синхронизация отдела '{department_key}'...")
        success = await sync.sync_department_members(department_key)
        
        if success:
            print(f"✅ Отдел '{department_key}' успешно синхронизирован")
        else:
            print(f"❌ Ошибка синхронизации отдела '{department_key}'")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def sync_all_departments():
    """Синхронизирует все отделы"""
    try:
        sync = TelegramGroupSync()
        results = await sync.sync_all_departments()
        
        print("🔄 Результаты синхронизации всех отделов:")
        for department, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {department}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def show_department_diff(department_key: str):
    """Показывает различия для конкретного отдела"""
    try:
        sync = TelegramGroupSync()
        diff = await sync.get_department_diff(department_key)
        
        if "error" in diff:
            print(f"❌ Ошибка: {diff['error'][0]}")
            return
        
        print(f"📊 Анализ отдела '{department_key}':")
        print(f"  📋 В конфигурации: {len(diff['config_members'])} участников")
        print(f"  👥 В группе: {len(diff['real_members'])} участников")
        
        if diff["missing_in_config"]:
            print(f"  ➕ Отсутствуют в конфигурации: {diff['missing_in_config']}")
        if diff["extra_in_config"]:
            print(f"  ➖ Лишние в конфигурации: {diff['extra_in_config']}")
        if not diff["missing_in_config"] and not diff["extra_in_config"]:
            print("  ✅ Конфигурация актуальна")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Синхронизация отделов с Telegram-группами")
    parser.add_argument("action", choices=["sync-all", "sync", "diff", "info"], 
                       help="Действие: sync-all (все отделы), sync (конкретный отдел), diff (различия), info (информация)")
    parser.add_argument("--department", "-d", help="Ключ отдела для sync/diff")
    
    args = parser.parse_args()
    
    if args.action == "info":
        print_department_info()
    elif args.action == "sync-all":
        asyncio.run(sync_all_departments())
    elif args.action == "sync":
        if not args.department:
            print("❌ Укажите отдел: --department <ключ_отдела>")
            return
        asyncio.run(sync_specific_department(args.department))
    elif args.action == "diff":
        if not args.department:
            print("❌ Укажите отдел: --department <ключ_отдела>")
            return
        asyncio.run(show_department_diff(args.department))

if __name__ == "__main__":
    main() 