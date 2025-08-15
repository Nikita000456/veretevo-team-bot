import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_PATH = os.path.join(BASE_DIR, 'data/tasks.json')
DEPARTMENTS_PATH = os.path.join(BASE_DIR, 'config_veretevo', 'departments_config.json')

# Загрузка отделов
with open(DEPARTMENTS_PATH, 'r', encoding='utf-8') as f:
    departments = json.load(f)

# Маппинг: user_id -> department
user_to_department = {}
for dep_key, dep in departments.items():
    for uid in dep.get('members', {}):
        user_to_department[uid] = dep_key

# Загрузка задач
with open(TASKS_PATH, 'r', encoding='utf-8') as f:
    tasks = json.load(f)

changed = 0
for task in tasks:
    # Если поле уже есть — пропускаем
    if 'department' in task:
        continue
    dep = None
    # Пробуем по assistant_id
    if task.get('assistant_id') is not None:
        dep = user_to_department.get(str(task['assistant_id']))
    # Если не нашли — пробуем по author_id
    if not dep and task.get('author_id') is not None:
        dep = user_to_department.get(str(task['author_id']))
    if dep:
        task['department'] = dep
        changed += 1

with open(TASKS_PATH, 'w', encoding='utf-8') as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)

print(f'Готово! Добавлено поле department в {changed} задач.') 