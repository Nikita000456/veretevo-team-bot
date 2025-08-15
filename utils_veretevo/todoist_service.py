import os
import requests
from datetime import datetime, date
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')
TODOIST_API_URL = 'https://api.todoist.com/rest/v2'
TODOIST_PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')

HEADERS = {
    'Authorization': f'Bearer {TODOIST_API_TOKEN}',
    'Content-Type': 'application/json',
}

# Таймауты для HTTP запросов
TIMEOUT = 10  # 10 секунд на запрос

def create_task(content, description=None):
    data = {'content': content}
    if description:
        data['description'] = description
    if TODOIST_PROJECT_ID:
        data['project_id'] = TODOIST_PROJECT_ID
    
    # Устанавливаем срок на день создания задачи
    today = date.today()
    data['due_date'] = today.isoformat()
    
    response = requests.post(f'{TODOIST_API_URL}/tasks', json=data, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()['id']

def close_task(task_id):
    response = requests.post(f'{TODOIST_API_URL}/tasks/{task_id}/close', headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.status_code == 204

def delete_task(task_id):
    response = requests.delete(f'{TODOIST_API_URL}/tasks/{task_id}', headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.status_code == 204

def add_comment(task_id, content):
    data = {'task_id': task_id, 'content': content}
    response = requests.post(f'{TODOIST_API_URL}/comments', json=data, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()['id']

def get_task(task_id):
    response = requests.get(f'{TODOIST_API_URL}/tasks/{task_id}', headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_comments(task_id):
    response = requests.get(f'{TODOIST_API_URL}/comments?task_id={task_id}', headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_director_tasks_from_todoist():
    try:
        params = {}
        if TODOIST_PROJECT_ID:
            params['project_id'] = TODOIST_PROJECT_ID
        response = requests.get(f'{TODOIST_API_URL}/tasks', headers=HEADERS, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        tasks = response.json()
        result = []
        for t in tasks:
            print(f"DEBUG: Задача из Todoist: {t}")
            try:
                comments = get_comments(t['id'])
                result.append({
                    'id': t['id'],
                    'content': t.get('content', 'Без названия'),
                    'status': 'завершено' if t.get('is_completed') else 'в работе',
                    'comments': comments,
                })
            except Exception as e:
                print(f"Ошибка при получении комментариев для задачи {t['id']}: {e}")
                # Добавляем задачу без комментариев
                result.append({
                    'id': t['id'],
                    'content': t.get('content', 'Без названия'),
                    'status': 'завершено' if t.get('is_completed') else 'в работе',
                    'comments': [],
                })
        return result
    except Exception as e:
        print(f"Ошибка при получении задач из Todoist: {e}")
        return [] 