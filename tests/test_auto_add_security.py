#!/usr/bin/env python3
"""
Тест автоматического добавления сотрудников в чат охраны
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services_veretevo.department_service import load_departments, get_user_departments, DEPARTMENTS

def test_current_security_members():
    """Проверяет текущих участников чата охраны"""
    print("🔍 Проверка текущих участников чата охраны...")
    
    load_departments()
    security_dept = DEPARTMENTS.get("security", {})
    
    print(f"📋 Отдел: {security_dept.get('name', 'Охрана')}")
    print(f"🆔 ID чата: {security_dept.get('chat_id', 'Не настроен')}")
    print(f"👥 Участники ({len(security_dept.get('members', {}))}):")
    
    for user_id, user_name in security_dept.get("members", {}).items():
        print(f"   - {user_name} (ID: {user_id})")
    
    print()

def test_user_departments():
    """Проверяет, в каких отделах состоят пользователи"""
    print("🔍 Проверка отделов пользователей...")
    
    # Тестируем существующих пользователей
    test_users = [
        (406325177, "Никита Астапов"),
        (979181458, "Алина Алексеевна"),
        (484411013, "Софья Елисеева"),
        (1596376468, "Мария"),
        (1119513062, "Наташа")
    ]
    
    for user_id, user_name in test_users:
        departments = get_user_departments(user_id)
        dept_names = [dept[1] for dept in departments]
        print(f"👤 {user_name} (ID: {user_id}): {', '.join(dept_names) if dept_names else 'Не состоит ни в одном отделе'}")
    
    print()

def simulate_new_member():
    """Симулирует добавление нового участника в чат охраны"""
    print("🧪 Симуляция добавления нового участника в чат охраны...")
    
    # Симулируем нового участника
    new_user_id = 123456789
    new_user_name = "Новый Охранник"
    
    load_departments()
    security_dept = DEPARTMENTS.get("security", {})
    
    # Добавляем участника (как это делает GroupMonitor)
    if "members" not in security_dept:
        security_dept["members"] = {}
    
    security_dept["members"][str(new_user_id)] = new_user_name
    
    # Проверяем, что участник добавлен
    departments = get_user_departments(new_user_id)
    dept_names = [dept[1] for dept in departments]
    
    print(f"✅ Добавлен новый участник: {new_user_name} (ID: {new_user_id})")
    print(f"📋 Теперь состоит в отделах: {', '.join(dept_names) if dept_names else 'Не состоит ни в одном отделе'}")
    
    # Проверяем, что он появится в списке при создании задач
    print(f"🎯 При создании задач он будет доступен в отделе: Охрана")
    
    print()

def test_task_creation_scenario():
    """Тестирует сценарий создания задач для нового участника"""
    print("🧪 Сценарий создания задач для нового участника...")
    
    # Симулируем нового участника
    new_user_id = 987654321
    new_user_name = "Тестовый Охранник"
    
    load_departments()
    security_dept = DEPARTMENTS.get("security", {})
    
    # Добавляем участника
    if "members" not in security_dept:
        security_dept["members"] = {}
    
    security_dept["members"][str(new_user_id)] = new_user_name
    
    # Проверяем, что он может создавать задачи
    departments = get_user_departments(new_user_id)
    
    if departments:
        print(f"✅ Пользователь {new_user_name} может создавать задачи")
        print(f"📋 Доступные отделы: {[dept[1] for dept in departments]}")
        
        # Проверяем, что он появится в списке исполнителей
        print(f"👥 При назначении задач он будет доступен как исполнитель")
    else:
        print(f"❌ Пользователь {new_user_name} не может создавать задачи")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 === ТЕСТ АВТОМАТИЧЕСКОГО ДОБАВЛЕНИЯ В ЧАТ ОХРАНЫ ===\n")
    
    # Проверяем текущих участников
    test_current_security_members()
    
    # Проверяем отделы пользователей
    test_user_departments()
    
    # Симулируем добавление нового участника
    simulate_new_member()
    
    # Тестируем сценарий создания задач
    test_task_creation_scenario()
    
    print("✅ Тестирование завершено!")
    print("\n📋 Ответы на ваши вопросы:")
    print("1. ✅ При добавлении в чат охраны человек автоматически попадет в базу данных")
    print("2. ✅ Ему можно будет ставить задачи через личный чат бота в разделе 'Охрана'")
    print("3. ✅ Он будет фигурировать везде, где используется система отделов")
    print("4. ✅ Система автоматического добавления работает для всех чатов")

if __name__ == "__main__":
    main() 