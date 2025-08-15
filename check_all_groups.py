#!/usr/bin/env python3
"""
Скрипт для проверки статуса всех групп
"""
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def check_group_status(chat_id, name):
    """Проверяет статус группы"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    data = {"chat_id": chat_id}
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                chat_info = result['result']
                return {
                    'status': 'active',
                    'title': chat_info.get('title', 'Название не найдено'),
                    'type': chat_info.get('type', 'тип не найден'),
                    'member_count': chat_info.get('member_count', 'неизвестно')
                }
            else:
                return {
                    'status': 'error',
                    'error': result.get('description', 'неизвестная ошибка'),
                    'code': result.get('error_code', 'неизвестно')
                }
        else:
            return {
                'status': 'http_error',
                'error': f'HTTP {response.status_code}',
                'code': response.status_code
            }
    except Exception as e:
        return {
            'status': 'exception',
            'error': str(e),
            'code': 'exception'
        }

def main():
    """Основная функция"""
    print("🔍 === ПРОВЕРКА СТАТУСА ВСЕХ ГРУПП ===\n")
    
    # Загружаем конфигурацию
    with open('config_veretevo/departments_config.json', 'r', encoding='utf-8') as f:
        DEPARTMENTS = json.load(f)
    
    # Проверяем все группы
    for key, dept in DEPARTMENTS.items():
        name = dept['name']
        chat_id = dept.get('chat_id')
        
        print(f"🏢 {name} ({key}):")
        if chat_id:
            print(f"   ID: {chat_id}")
            status = check_group_status(chat_id, name)
            
            if status['status'] == 'active':
                print(f"   ✅ Статус: Активна")
                print(f"   📝 Название: {status['title']}")
                print(f"   🔢 Тип: {status['type']}")
                print(f"   👥 Участников: {status['member_count']}")
            else:
                print(f"   ❌ Статус: {status['status']}")
                print(f"   🚫 Ошибка: {status['error']}")
                if 'code' in status and status['code'] != 'exception':
                    print(f"   🔢 Код ошибки: {status['code']}")
        else:
            print(f"   ⚠️ ID чата не настроен")
        
        print()

if __name__ == "__main__":
    main()

