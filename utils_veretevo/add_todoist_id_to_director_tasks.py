import json
import os

GENERAL_DIRECTOR_ID = 406325177

TASKS_PATH = os.path.join(os.path.dirname(__file__), '../data/tasks.json')
TASKS_PATH = os.path.abspath(TASKS_PATH)

with open(TASKS_PATH, 'r', encoding='utf-8') as f:
    tasks = json.load(f)

changed = False
for task in tasks:
    if task.get('assistant_id') == GENERAL_DIRECTOR_ID:
        if 'todoist_task_id' not in task:
            task['todoist_task_id'] = None
            changed = True

if changed:
    with open(TASKS_PATH, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print('tasks.json обновлён: добавлены поля todoist_task_id для задач директора.')
else:
    print('Изменений не требуется: все задачи директора уже содержат поле todoist_task_id.') 