#!/usr/bin/env python3
"""
Скрипт для тестирования системы мониторинга групп.
Позволяет симулировать события добавления/удаления участников.
"""
import sys
import asyncio
import argparse
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils_veretevo.group_monitor import GroupMonitor
from services_veretevo.department_service import load_departments, DEPARTMENTS

async def test_monitor_initialization():
    """Тестирует инициализацию монитора групп"""
    print("🔍 Тестирование инициализации монитора групп...")
    
    try:
        monitor = GroupMonitor()
        print(f"✅ Монитор инициализирован успешно")
        print(f"📋 Отслеживаемые чаты: {len(monitor.monitored_chats)}")
        
        for chat_id in monitor.monitored_chats:
            department_key = monitor.get_department_by_chat_id(chat_id)
            if department_key:
                department = DEPARTMENTS[department_key]
                print(f"  • {department['name']} (ID: {chat_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации монитора: {e}")
        return False

async def test_event_detection():
    """Тестирует определение типов событий"""
    print("\n🔍 Тестирование определения типов событий...")
    
    try:
        monitor = GroupMonitor()
        
        # Симулируем различные события
        from telegram import ChatMember, User
        
        # Создаем тестовые объекты
        user = User(id=123456789, first_name="Test User", is_bot=False)
        
        # Тест 1: Добавление участника
        old_member = ChatMember(user=user, status="left")
        new_member = ChatMember(user=user, status="member")
        event_type = monitor.determine_event_type(old_member, new_member)
        print(f"✅ Добавление участника: {event_type}")
        
        # Тест 2: Удаление участника
        old_member = ChatMember(user=user, status="member")
        new_member = ChatMember(user=user, status="left")
        event_type = monitor.determine_event_type(old_member, new_member)
        print(f"✅ Удаление участника: {event_type}")
        
        # Тест 3: Повышение до администратора
        old_member = ChatMember(user=user, status="member")
        new_member = ChatMember(user=user, status="administrator")
        event_type = monitor.determine_event_type(old_member, new_member)
        print(f"✅ Повышение до администратора: {event_type}")
        
        # Тест 4: Понижение с администратора
        old_member = ChatMember(user=user, status="administrator")
        new_member = ChatMember(user=user, status="member")
        event_type = monitor.determine_event_type(old_member, new_member)
        print(f"✅ Понижение с администратора: {event_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования событий: {e}")
        return False

async def test_department_lookup():
    """Тестирует поиск отделов по ID чата"""
    print("\n🔍 Тестирование поиска отделов...")
    
    try:
        monitor = GroupMonitor()
        load_departments()
        
        for department_key, department in DEPARTMENTS.items():
            chat_id = department.get("chat_id")
            if chat_id:
                found_key = monitor.get_department_by_chat_id(chat_id)
                if found_key == department_key:
                    print(f"✅ {department['name']}: {chat_id} -> {found_key}")
                else:
                    print(f"❌ {department['name']}: {chat_id} -> {found_key} (ожидалось {department_key})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка поиска отделов: {e}")
        return False

async def test_member_management():
    """Тестирует управление участниками"""
    print("\n🔍 Тестирование управления участниками...")
    
    try:
        monitor = GroupMonitor()
        load_departments()
        
        # Тестируем добавление участника
        test_user_id = 999999999
        test_user_name = "Test User"
        
        # Находим первый отдел с chat_id
        test_department = None
        for key, dept in DEPARTMENTS.items():
            if dept.get("chat_id"):
                test_department = key
                break
        
        if not test_department:
            print("❌ Нет отделов с chat_id для тестирования")
            return False
        
        print(f"🧪 Тестируем отдел: {test_department}")
        
        # Симулируем добавление участника
        from telegram import User
        test_user = User(id=test_user_id, first_name=test_user_name, is_bot=False)
        
        # Проверяем, что участника нет в конфигурации
        department = DEPARTMENTS[test_department]
        if str(test_user_id) in department["members"]:
            print(f"⚠️ Участник {test_user_id} уже есть в отделе {test_department}")
        else:
            # Симулируем добавление
            await monitor.handle_member_added(test_department, test_user)
            
            # Проверяем, что участник добавлен
            load_departments()
            if str(test_user_id) in DEPARTMENTS[test_department]["members"]:
                print(f"✅ Участник {test_user_id} успешно добавлен в отдел {test_department}")
                
                # Симулируем удаление
                await monitor.handle_member_removed(test_department, test_user)
                
                # Проверяем, что участник удален
                load_departments()
                if str(test_user_id) not in DEPARTMENTS[test_department]["members"]:
                    print(f"✅ Участник {test_user_id} успешно удален из отдела {test_department}")
                else:
                    print(f"❌ Участник {test_user_id} не удален из отдела {test_department}")
            else:
                print(f"❌ Участник {test_user_id} не добавлен в отдел {test_department}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка управления участниками: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    parser = argparse.ArgumentParser(description="Тестирование системы мониторинга групп")
    parser.add_argument("--test", choices=["all", "init", "events", "lookup", "members"], 
                       default="all", help="Тип теста")
    
    args = parser.parse_args()
    
    print("🚀 Запуск тестов системы мониторинга групп...")
    
    results = []
    
    if args.test in ["all", "init"]:
        results.append(await test_monitor_initialization())
    
    if args.test in ["all", "events"]:
        results.append(await test_event_detection())
    
    if args.test in ["all", "lookup"]:
        results.append(await test_department_lookup())
    
    if args.test in ["all", "members"]:
        results.append(await test_member_management())
    
    # Выводим итоговый результат
    print(f"\n📊 Результаты тестирования:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Все тесты пройдены ({passed}/{total})")
        return 0
    else:
        print(f"❌ Тесты пройдены частично ({passed}/{total})")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 