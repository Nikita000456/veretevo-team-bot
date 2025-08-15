#!/usr/bin/env python3
"""
Скрипт для установки cron задачи очистки завершенных задач.
Запускает очистку раз в неделю по воскресеньям в 2:00 утра.
"""

import os
import subprocess
import sys
from datetime import datetime

def install_cleanup_cron():
    """Устанавливает cron задачу для очистки задач"""
    
    # Получаем абсолютный путь к скрипту очистки
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    cleanup_script = os.path.join(project_dir, "scripts", "cleanup_tasks.py")
    
    # Проверяем, что скрипт очистки существует
    if not os.path.exists(cleanup_script):
        print(f"❌ Ошибка: скрипт очистки не найден: {cleanup_script}")
        return False
    
    # Cron задача: каждое воскресенье в 2:00 утра
    cron_job = f"0 2 * * 0 cd {project_dir} && python3 scripts/cleanup_tasks.py >> logs/cleanup_cron.log 2>&1"
    
    try:
        # Получаем текущие cron задачи
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Проверяем, есть ли уже наша задача
        if cron_job in current_crontab:
            print("✅ Cron задача для очистки задач уже установлена")
            return True
        
        # Добавляем новую задачу
        new_crontab = current_crontab + "\n" + cron_job + "\n"
        
        # Устанавливаем обновленный crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron задача успешно установлена")
            print(f"📅 Очистка задач будет запускаться каждое воскресенье в 2:00 утра")
            print(f"📝 Логи будут записываться в: {project_dir}/logs/cleanup_cron.log")
            return True
        else:
            print("❌ Ошибка при установке cron задачи")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def remove_cleanup_cron():
    """Удаляет cron задачу очистки задач"""
    
    try:
        # Получаем текущие cron задачи
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ℹ️ Нет установленных cron задач")
            return True
        
        current_crontab = result.stdout
        
        # Удаляем строки с нашим скриптом очистки
        lines = current_crontab.split('\n')
        filtered_lines = []
        
        for line in lines:
            if 'cleanup_tasks.py' not in line and line.strip():
                filtered_lines.append(line)
        
        if len(filtered_lines) == len(lines):
            print("ℹ️ Cron задача для очистки задач не найдена")
            return True
        
        # Устанавливаем обновленный crontab
        new_crontab = '\n'.join(filtered_lines) + '\n'
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron задача очистки задач удалена")
            return True
        else:
            print("❌ Ошибка при удалении cron задачи")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def show_cron_status():
    """Показывает статус cron задач"""
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Текущие cron задачи:")
            print(result.stdout)
        else:
            print("ℹ️ Нет установленных cron задач")
            
    except Exception as e:
        print(f"❌ Ошибка при получении cron задач: {e}")

def main():
    """Основная функция"""
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 setup_cleanup_cron.py install   # Установить cron задачу")
        print("  python3 setup_cleanup_cron.py remove    # Удалить cron задачу")
        print("  python3 setup_cleanup_cron.py status    # Показать статус")
        return
    
    command = sys.argv[1].lower()
    
    if command == "install":
        if install_cleanup_cron():
            print("\n🎉 Настройка завершена успешно!")
            print("💡 Для проверки статуса используйте: python3 setup_cleanup_cron.py status")
        else:
            print("\n❌ Настройка не удалась")
            sys.exit(1)
    
    elif command == "remove":
        if remove_cleanup_cron():
            print("\n✅ Cron задача удалена")
        else:
            print("\n❌ Ошибка при удалении")
            sys.exit(1)
    
    elif command == "status":
        show_cron_status()
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 