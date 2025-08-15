#!/usr/bin/env python3
"""
Скрипт для настройки автоматической синхронизации отделов по расписанию.
Создает cron-задачи для регулярной синхронизации.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_cron_available():
    """Проверяет доступность cron"""
    try:
        result = subprocess.run(['which', 'crontab'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def get_project_path():
    """Получает абсолютный путь к проекту"""
    return Path(__file__).parent.parent.absolute()

def create_cron_jobs():
    """Создает cron-задачи для автоматической синхронизации"""
    project_path = get_project_path()
    
    # Пути к скриптам
    auto_sync_script = project_path / "scripts" / "auto_sync_departments.py"
    python_path = sys.executable
    
    # Создаем cron-задачи
    cron_jobs = [
        # Ежедневная синхронизация в 6:00 утра
        f"0 6 * * * cd {project_path} && {python_path} {auto_sync_script} --backup >> logs/cron_sync.log 2>&1",
        
        # Синхронизация каждые 4 часа (6:00, 10:00, 14:00, 18:00, 22:00)
        f"0 10,14,18,22 * * * cd {project_path} && {python_path} {auto_sync_script} >> logs/cron_sync.log 2>&1",
        
        # Анализ различий каждые 2 часа
        f"0 */2 * * * cd {project_path} && {python_path} {auto_sync_script} --dry-run >> logs/cron_diff.log 2>&1"
    ]
    
    return cron_jobs

def install_cron_jobs():
    """Устанавливает cron-задачи"""
    if not check_cron_available():
        print("❌ Cron не доступен в системе")
        return False
    
    try:
        # Получаем текущие cron-задачи
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Создаем новые задачи
        new_jobs = create_cron_jobs()
        
        # Добавляем новые задачи к существующим
        updated_cron = current_cron + "\n".join([
            "# Автоматическая синхронизация отделов Veretevo Bot",
            "# Добавлено автоматически",
            ""
        ] + new_jobs + [""])
        
        # Временно сохраняем в файл
        temp_cron_file = "/tmp/veretevo_cron"
        with open(temp_cron_file, 'w') as f:
            f.write(updated_cron)
        
        # Устанавливаем новые cron-задачи
        subprocess.run(['crontab', temp_cron_file], check=True)
        
        # Удаляем временный файл
        os.remove(temp_cron_file)
        
        print("✅ Cron-задачи установлены успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка установки cron-задач: {e}")
        return False

def remove_cron_jobs():
    """Удаляет cron-задачи для автоматической синхронизации"""
    if not check_cron_available():
        print("❌ Cron не доступен в системе")
        return False
    
    try:
        # Получаем текущие cron-задачи
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Не удалось получить текущие cron-задачи")
            return False
        
        current_cron = result.stdout
        lines = current_cron.split('\n')
        
        # Удаляем строки, связанные с Veretevo Bot
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            if "# Автоматическая синхронизация отделов Veretevo Bot" in line:
                skip_next = True
                continue
            elif skip_next and line.strip() == "":
                skip_next = False
                continue
            elif skip_next:
                continue
            else:
                filtered_lines.append(line)
        
        # Создаем новый cron без задач Veretevo Bot
        new_cron = '\n'.join(filtered_lines)
        
        # Временно сохраняем в файл
        temp_cron_file = "/tmp/veretevo_cron_clean"
        with open(temp_cron_file, 'w') as f:
            f.write(new_cron)
        
        # Устанавливаем очищенные cron-задачи
        subprocess.run(['crontab', temp_cron_file], check=True)
        
        # Удаляем временный файл
        os.remove(temp_cron_file)
        
        print("✅ Cron-задачи удалены успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка удаления cron-задач: {e}")
        return False

def show_cron_jobs():
    """Показывает текущие cron-задачи"""
    if not check_cron_available():
        print("❌ Cron не доступен в системе")
        return False
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 Текущие cron-задачи:")
            print(result.stdout)
        else:
            print("📋 Нет установленных cron-задач")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения cron-задач: {e}")
        return False

def create_systemd_service():
    """Создает systemd сервис для автоматического запуска"""
    project_path = get_project_path()
    
    service_content = f"""[Unit]
Description=Veretevo Bot Auto Sync Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={project_path}
ExecStart={sys.executable} {project_path}/scripts/auto_sync_departments.py --backup
Restart=always
RestartSec=3600

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "/etc/systemd/system/veretevo-auto-sync.service"
    
    try:
        # Создаем файл сервиса
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Перезагружаем systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        # Включаем автозапуск
        subprocess.run(['sudo', 'systemctl', 'enable', 'veretevo-auto-sync.service'], check=True)
        
        print("✅ Systemd сервис создан и включен")
        print(f"📁 Файл сервиса: {service_file}")
        print("🔧 Команды управления:")
        print("  sudo systemctl start veretevo-auto-sync.service")
        print("  sudo systemctl stop veretevo-auto-sync.service")
        print("  sudo systemctl status veretevo-auto-sync.service")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания systemd сервиса: {e}")
        return False

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Настройка автоматической синхронизации отделов")
    parser.add_argument("action", choices=["install", "remove", "show", "systemd"], 
                       help="Действие: install (установить), remove (удалить), show (показать), systemd (создать сервис)")
    
    args = parser.parse_args()
    
    if args.action == "install":
        print("🚀 Установка автоматической синхронизации...")
        success = install_cron_jobs()
        if success:
            print("\n✅ Автоматическая синхронизация настроена!")
            print("📅 Расписание:")
            print("  • Ежедневная синхронизация в 6:00 (с резервной копией)")
            print("  • Синхронизация каждые 4 часа (10:00, 14:00, 18:00, 22:00)")
            print("  • Анализ различий каждые 2 часа")
            print("\n📋 Логи:")
            print("  • logs/cron_sync.log - логи синхронизации")
            print("  • logs/cron_diff.log - логи анализа различий")
    
    elif args.action == "remove":
        print("🗑️ Удаление автоматической синхронизации...")
        success = remove_cron_jobs()
        if success:
            print("✅ Автоматическая синхронизация удалена")
    
    elif args.action == "show":
        show_cron_jobs()
    
    elif args.action == "systemd":
        print("🔧 Создание systemd сервиса...")
        create_systemd_service()

if __name__ == "__main__":
    import argparse
    main() 