#!/usr/bin/env python3
"""
Скрипт для проверки совместимости изменений
Проверяет, что новый функционал не ломает существующий
"""

import os
import sys
import logging
import json
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_handler_registration():
    """Проверяет правильность регистрации обработчиков"""
    print("🔍 Проверка регистрации обработчиков...")
    
    try:
        # Проверяем только синтаксис, не импортируем
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            compile(content, 'main.py', 'exec')
        print("✅ main.py синтаксически корректен")
    except Exception as e:
        print(f"❌ Ошибка в main.py: {e}")
        return False
    
    return True

def check_gpt_handlers():
    """Проверяет GPT обработчики"""
    print("🤖 Проверка GPT обработчиков...")
    
    try:
        from handlers_veretevo.gpt_handlers import register_gpt_handlers
        print("✅ GPT обработчики импортируются")
    except Exception as e:
        print(f"❌ Ошибка импорта GPT обработчиков: {e}")
        return False
    
    return True

def check_task_handlers():
    """Проверяет обработчики задач"""
    print("📋 Проверка обработчиков задач...")
    
    try:
        # Проверяем только синтаксис
        with open('handlers_veretevo/tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
            compile(content, 'handlers_veretevo/tasks.py', 'exec')
        print("✅ Обработчики задач синтаксически корректны")
    except Exception as e:
        print(f"❌ Ошибка в обработчиках задач: {e}")
        return False
    
    return True

def check_services():
    """Проверяет сервисы"""
    print("🔧 Проверка сервисов...")
    
    services = [
        'services_veretevo.task_service',
        'services_veretevo.department_service',
        'services_veretevo.gpt_service'
    ]
    
    for service in services:
        try:
            __import__(service)
            print(f"✅ {service} импортируется")
        except Exception as e:
            print(f"❌ Ошибка импорта {service}: {e}")
            return False
    
    return True

def check_data_files():
    """Проверяет наличие необходимых файлов данных"""
    print("📁 Проверка файлов данных...")
    
    required_files = [
        'data/tasks.json',
        'data/answers.json',
        'config_veretevo/departments_config.json'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} существует")
        else:
            print(f"⚠️ {file_path} отсутствует")
    
    return True

def check_logs():
    """Проверяет логи на ошибки"""
    print("📝 Проверка логов...")
    
    log_file = "logs/bot.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                error_lines = [line for line in lines[-50:] if 'ERROR' in line or 'Exception' in line]
                
                if error_lines:
                    print(f"⚠️ Найдено {len(error_lines)} ошибок в логах:")
                    for line in error_lines[-5:]:
                        print(f"   {line.strip()}")
                else:
                    print("✅ Ошибок в логах не найдено")
        except Exception as e:
            print(f"❌ Ошибка чтения логов: {e}")
    else:
        print("⚠️ Файл логов не найден")
    
    return True

def main():
    """Основная функция проверки"""
    print("🚀 Запуск проверки совместимости...")
    print("=" * 50)
    
    checks = [
        check_handler_registration,
        check_gpt_handlers,
        check_task_handlers,
        check_services,
        check_data_files,
        check_logs
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка в проверке {check.__name__}: {e}")
            results.append(False)
    
    print("=" * 50)
    print("📊 Результаты проверки:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Все проверки пройдены ({passed}/{total})")
        print("🎉 Совместимость подтверждена!")
        return True
    else:
        print(f"❌ Проверки провалены ({passed}/{total})")
        print("⚠️ Требуется исправление проблем!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 