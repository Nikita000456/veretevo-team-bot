#!/usr/bin/env python3
"""
Скрипт для управления настройками уведомлений системы мониторинга групп.
Позволяет включать/отключать уведомления о изменениях в группах.
"""
import os
import sys
import argparse
from pathlib import Path

def get_env_file_path():
    """Получает путь к файлу .env"""
    project_root = Path(__file__).parent.parent
    return project_root / ".env"

def read_env_file():
    """Читает файл .env"""
    env_file = get_env_file_path()
    if not env_file.exists():
        return {}
    
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    return env_vars

def write_env_file(env_vars):
    """Записывает файл .env"""
    env_file = get_env_file_path()
    
    # Создаем директорию, если её нет
    env_file.parent.mkdir(exist_ok=True)
    
    with open(env_file, 'w', encoding='utf-8') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def enable_notifications():
    """Включает уведомления о изменениях в группах"""
    env_vars = read_env_file()
    env_vars['ENABLE_GROUP_NOTIFICATIONS'] = 'true'
    write_env_file(env_vars)
    print("✅ Уведомления о изменениях в группах включены")
    print("ℹ️ Перезапустите бота для применения изменений")

def disable_notifications():
    """Отключает уведомления о изменениях в группах"""
    env_vars = read_env_file()
    env_vars['ENABLE_GROUP_NOTIFICATIONS'] = 'false'
    write_env_file(env_vars)
    print("🔇 Уведомления о изменениях в группах отключены")
    print("ℹ️ Перезапустите бота для применения изменений")

def show_status():
    """Показывает текущий статус уведомлений"""
    env_vars = read_env_file()
    current_setting = env_vars.get('ENABLE_GROUP_NOTIFICATIONS', 'true')
    
    print("📊 Статус уведомлений о изменениях в группах:")
    if current_setting.lower() == 'true':
        print("✅ ВКЛЮЧЕНЫ")
        print("   Система будет отправлять уведомления при:")
        print("   • Добавлении новых участников")
        print("   • Удалении участников")
        print("   • Повышении/понижении администраторов")
    else:
        print("🔇 ОТКЛЮЧЕНЫ")
        print("   Система работает в тихом режиме")
        print("   Изменения только логируются, уведомления не отправляются")
    
    print(f"\n📁 Файл настроек: {get_env_file_path()}")

def test_notification():
    """Тестирует отправку уведомления"""
    import asyncio
    from pathlib import Path
    
    # Добавляем корневую директорию проекта в путь
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from utils_veretevo.group_monitor import GroupMonitor
    from services_veretevo.department_service import load_departments, DEPARTMENTS
    
    async def send_test_notification():
        """Отправляет тестовое уведомление"""
        try:
            monitor = GroupMonitor(enable_notifications=True)
            load_departments()
            
            # Находим первый отдел с chat_id
            test_department = None
            for key, dept in DEPARTMENTS.items():
                if dept.get("chat_id"):
                    test_department = key
                    break
            
            if not test_department:
                print("❌ Нет отделов с chat_id для тестирования")
                return
            
            print(f"🧪 Отправляем тестовое уведомление в отдел: {test_department}")
            
            # Отправляем тестовое уведомление
            await monitor.notify_admins(test_department, "🧪 Это тестовое уведомление от системы мониторинга")
            
            print("✅ Тестовое уведомление отправлено")
            
        except Exception as e:
            print(f"❌ Ошибка отправки тестового уведомления: {e}")
    
    asyncio.run(send_test_notification())

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Управление уведомлениями системы мониторинга групп")
    parser.add_argument("action", choices=["enable", "disable", "status", "test"], 
                       help="Действие: enable (включить), disable (отключить), status (статус), test (тест)")
    
    args = parser.parse_args()
    
    if args.action == "enable":
        enable_notifications()
    elif args.action == "disable":
        disable_notifications()
    elif args.action == "status":
        show_status()
    elif args.action == "test":
        test_notification()

if __name__ == "__main__":
    main() 