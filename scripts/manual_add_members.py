#!/usr/bin/env python3
"""
Скрипт для ручного добавления участников в конфигурацию отделов.
Используется когда автоматическая синхронизация не может получить всех участников.
"""
import sys
import json
import argparse
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_veretevo.constants import DEPARTMENTS_JSON_PATH
from services_veretevo.department_service import load_departments, save_departments, DEPARTMENTS

def add_member_to_department(department_key: str, user_id: int, user_name: str):
    """Добавляет участника в отдел"""
    load_departments()
    
    if department_key not in DEPARTMENTS:
        print(f"❌ Отдел '{department_key}' не найден")
        return False
    
    department = DEPARTMENTS[department_key]
    user_id_str = str(user_id)
    
    # Добавляем участника
    department["members"][user_id_str] = user_name
    
    # Сохраняем изменения
    save_departments()
    
    print(f"✅ Добавлен участник {user_name} (ID: {user_id}) в отдел '{department_key}'")
    return True

def remove_member_from_department(department_key: str, user_id: int):
    """Удаляет участника из отдела"""
    load_departments()
    
    if department_key not in DEPARTMENTS:
        print(f"❌ Отдел '{department_key}' не найден")
        return False
    
    department = DEPARTMENTS[department_key]
    user_id_str = str(user_id)
    
    if user_id_str not in department["members"]:
        print(f"❌ Участник с ID {user_id} не найден в отделе '{department_key}'")
        return False
    
    user_name = department["members"][user_id_str]
    del department["members"][user_id_str]
    
    # Сохраняем изменения
    save_departments()
    
    print(f"✅ Удален участник {user_name} (ID: {user_id}) из отдела '{department_key}'")
    return True

def list_department_members(department_key: str):
    """Показывает список участников отдела"""
    load_departments()
    
    if department_key not in DEPARTMENTS:
        print(f"❌ Отдел '{department_key}' не найден")
        return
    
    department = DEPARTMENTS[department_key]
    members = department.get("members", {})
    
    print(f"📋 Участники отдела '{department_key}' ({department['name']}):")
    if members:
        for user_id, name in members.items():
            print(f"  • {name} (ID: {user_id})")
    else:
        print("  (нет участников)")

def add_from_file(department_key: str, file_path: str):
    """Добавляет участников из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ Файл должен содержать список участников")
            return False
        
        success_count = 0
        for member in data:
            if isinstance(member, dict) and 'id' in member and 'name' in member:
                if add_member_to_department(department_key, member['id'], member['name']):
                    success_count += 1
            else:
                print(f"❌ Неверный формат участника: {member}")
        
        print(f"✅ Добавлено {success_count} участников в отдел '{department_key}'")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Ручное управление участниками отделов")
    parser.add_argument("action", choices=["add", "remove", "list", "add-from-file"], 
                       help="Действие: add, remove, list, add-from-file")
    parser.add_argument("--department", "-d", required=True, help="Ключ отдела")
    parser.add_argument("--user-id", "-u", type=int, help="ID пользователя")
    parser.add_argument("--name", "-n", help="Имя пользователя")
    parser.add_argument("--file", "-f", help="Путь к файлу с участниками (для add-from-file)")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_department_members(args.department)
    elif args.action == "add":
        if not args.user_id or not args.name:
            print("❌ Укажите --user-id и --name для добавления участника")
            return
        add_member_to_department(args.department, args.user_id, args.name)
    elif args.action == "remove":
        if not args.user_id:
            print("❌ Укажите --user-id для удаления участника")
            return
        remove_member_from_department(args.department, args.user_id)
    elif args.action == "add-from-file":
        if not args.file:
            print("❌ Укажите --file для добавления из файла")
            return
        add_from_file(args.department, args.file)

if __name__ == "__main__":
    main() 