#!/usr/bin/env python3
"""
Скрипт для очистки задач со статусом "отменено" и "завершено"
Удаляет все задачи с этими статусами из файла tasks.json
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """Создает резервную копию файла"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Создана резервная копия: {backup_path}")
    return backup_path

def clean_tasks_file(file_path):
    """Очищает файл от задач со статусом 'отменено' и 'завершено'"""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return
    
    print(f"\n🔍 Обрабатываю файл: {file_path}")
    
    # Создаем резервную копию
    backup_path = backup_file(file_path)
    
    # Читаем данные
    with open(file_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print(f"📊 Всего задач в файле: {len(tasks)}")
    
    # Подсчитываем задачи по статусам
    status_counts = {}
    for task in tasks:
        status = task.get('status', 'неизвестно')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("📈 Статистика по статусам:")
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    
    # Фильтруем задачи
    original_count = len(tasks)
    tasks = [task for task in tasks if task.get('status') not in ['отменено', 'завершено']]
    removed_count = original_count - len(tasks)
    
    print(f"🗑️  Удалено задач: {removed_count}")
    print(f"✅ Осталось задач: {len(tasks)}")
    
    # Сохраняем очищенные данные
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Файл обновлен: {file_path}")
    
    return removed_count

def main():
    """Основная функция"""
    print("🧹 Начинаю очистку задач...")
    
    # Пути к файлам
    data_dir = Path(__file__).parent.parent / "data"
    tasks_file = data_dir / "tasks.json"
    
    total_removed = 0
    
    # Очищаем основной файл задач
    if tasks_file.exists():
        removed = clean_tasks_file(tasks_file)
        total_removed += removed
    else:
        print(f"⚠️  Файл не найден: {tasks_file}")
    
    print(f"\n🎉 Очистка завершена!")
    print(f"📊 Всего удалено задач: {total_removed}")
    print("💡 Резервные копии созданы с временными метками")

if __name__ == "__main__":
    main() 