#!/usr/bin/env python3
"""
Скрипт для мониторинга работы cron очистки задач.
Показывает статистику и последние запуски.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

def check_cron_status():
    """Проверяет статус cron задач"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and 'cleanup_tasks.py' in result.stdout:
            print("✅ Cron задача очистки установлена")
            return True
        else:
            print("❌ Cron задача очистки не найдена")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки cron: {e}")
        return False

def check_log_files():
    """Проверяет файлы логов"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_dir, "logs")
    
    print("\n📋 Статус файлов логов:")
    
    # Проверяем основной лог очистки
    cleanup_log = os.path.join(logs_dir, "cleanup_tasks.log")
    if os.path.exists(cleanup_log):
        size = os.path.getsize(cleanup_log)
        mtime = datetime.fromtimestamp(os.path.getmtime(cleanup_log))
        print(f"✅ cleanup_tasks.log: {size} байт, изменен {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ cleanup_tasks.log: файл не найден")
    
    # Проверяем cron лог
    cron_log = os.path.join(logs_dir, "cleanup_cron.log")
    if os.path.exists(cron_log):
        size = os.path.getsize(cron_log)
        mtime = datetime.fromtimestamp(os.path.getmtime(cron_log))
        print(f"✅ cleanup_cron.log: {size} байт, изменен {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ cleanup_cron.log: файл не найден")

def show_recent_logs():
    """Показывает последние записи из логов"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_dir, "logs")
    
    print("\n📝 Последние записи из логов:")
    
    # Показываем последние записи из cron лога
    cron_log = os.path.join(logs_dir, "cleanup_cron.log")
    if os.path.exists(cron_log):
        print("\n🕐 Cron лог (последние 10 строк):")
        try:
            with open(cron_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Ошибка чтения cron лога: {e}")
    
    # Показываем последние записи из основного лога
    cleanup_log = os.path.join(logs_dir, "cleanup_tasks.log")
    if os.path.exists(cleanup_log):
        print("\n🧹 Основной лог очистки (последние 10 строк):")
        try:
            with open(cleanup_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Ошибка чтения основного лога: {e}")

def test_cleanup():
    """Тестирует очистку задач"""
    print("\n🧪 Тестирование очистки задач...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup_tasks.py")
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Тест очистки прошел успешно")
            if result.stdout:
                print("📤 Вывод:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"  {line}")
        else:
            print("❌ Тест очистки не прошел")
            if result.stderr:
                print("📤 Ошибки:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        print(f"  {line}")
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def main():
    """Основная функция мониторинга"""
    
    print("🔍 Мониторинг очистки задач Veretevo Team Bot")
    print("=" * 50)
    
    # Проверяем cron статус
    cron_ok = check_cron_status()
    
    # Проверяем файлы логов
    check_log_files()
    
    # Показываем последние логи
    show_recent_logs()
    
    # Тестируем очистку
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_cleanup()
    
    print("\n" + "=" * 50)
    if cron_ok:
        print("✅ Система очистки задач работает корректно")
        print("📅 Следующий запуск: воскресенье в 2:00 утра")
    else:
        print("⚠️ Рекомендуется установить cron задачу:")
        print("   python3 scripts/setup_cleanup_cron.py install")

if __name__ == "__main__":
    main() 