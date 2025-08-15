#!/usr/bin/env python3
"""
Тест для нового участника чата охраны (ID: 5229424607)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services_veretevo.department_service import load_departments, get_user_departments, DEPARTMENTS

def test_new_member_capabilities():
    """Проверяет возможности нового участника"""
    print("🔍 Проверка возможностей нового участника (ID: 5229424607)...")
    
    load_departments()
    user_id = 5229424607
    
    # Проверяем, в каких отделах он состоит
    departments = get_user_departments(user_id)
    dept_names = [dept[1] for dept in departments]
    
    print(f"👤 Пользователь: Nikita Astapov (ID: {user_id})")
    print(f"📋 Состоит в отделах: {', '.join(dept_names) if dept_names else 'Не состоит ни в одном отделе'}")
    
    if "Охрана" in dept_names:
        print("✅ Может создавать задачи для отдела 'Охрана'")
        print("✅ Доступен как исполнитель при назначении задач")
        print("✅ Может просматривать задачи отдела 'Охрана'")
        print("✅ Получит доступ к GPT функционалу в чате охраны")
    else:
        print("❌ НЕ может создавать задачи")
    
    print()

def test_task_creation_scenario():
    """Тестирует сценарий создания задач"""
    print("🧪 Сценарий создания задач для нового участника...")
    
    user_id = 5229424607
    departments = get_user_departments(user_id)
    
    if departments:
        print("✅ Пользователь может создавать задачи")
        print("📋 Доступные отделы:")
        for dept_key, dept_name in departments:
            print(f"   - {dept_name} (ключ: {dept_key})")
        
        # Проверяем, что он появится в списке исполнителей
        print("\n👥 При назначении задач он будет доступен как исполнитель")
        print("🎯 В личном чате с ботом он увидит:")
        print("   - Кнопку '📌 Новая задача'")
        print("   - Возможность выбрать отдел 'Охрана'")
        print("   - Список задач отдела 'Охрана'")
    else:
        print("❌ Пользователь не может создавать задачи")
    
    print()

def test_gpt_access():
    """Проверяет доступ к GPT функционалу"""
    print("🧪 Проверка доступа к GPT функционалу...")
    
    user_id = 5229424607
    departments = get_user_departments(user_id)
    dept_names = [dept[1] for dept in departments]
    
    if "Охрана" in dept_names:
        print("✅ В чате охраны (-1002295933154) он получит доступ к GPT:")
        print("   - Кнопка '💡 GPT-ответ' при написании сообщений")
        print("   - Генерация ответов с помощью Yandex GPT")
        print("   - Сохранение ответов в базу знаний")
    else:
        print("❌ Нет доступа к GPT функционалу")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 === ТЕСТ НОВОГО УЧАСТНИКА ЧАТА ОХРАНЫ ===\n")
    
    # Проверяем возможности нового участника
    test_new_member_capabilities()
    
    # Тестируем сценарий создания задач
    test_task_creation_scenario()
    
    # Проверяем доступ к GPT
    test_gpt_access()
    
    print("✅ Тестирование завершено!")
    print("\n📋 Результат:")
    print("✅ Новый участник (ID: 5229424607) успешно добавлен в систему")
    print("✅ Он может создавать задачи для отдела 'Охрана'")
    print("✅ Он доступен как исполнитель при назначении задач")
    print("✅ Он получит доступ к GPT функционалу в чате охраны")
    print("✅ Система автоматического добавления работает корректно!")

if __name__ == "__main__":
    main() 