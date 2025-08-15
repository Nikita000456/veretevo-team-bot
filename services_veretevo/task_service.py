"""
Модуль для работы с задачами. Содержит функции загрузки, сохранения, поиска и обновления задач.
"""
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from config_veretevo.constants import TASKS_FILE, TASK_STATUS_NEW, TASK_STATUS_ACTIVE, TASK_STATUS_IN_PROGRESS, TASK_STATUS_FINISHED, TASK_STATUS_CANCELLED, GENERAL_DIRECTOR_ID
import logging
import os

@dataclass
class Task:
    """
    Класс, представляющий задачу.

    Атрибуты:
        id (int): Уникальный идентификатор задачи.
        text (str): Текст задачи.
        media (dict|None): Медиафайл задачи.
        status (str): Статус задачи.
        author_id (int): ID автора.
        author_name (str): Имя автора.
        assistant_id (int|None): ID ассистента.
        assistant_name (str|None): Имя ассистента.
        department (str|None): Ключ отдела.
        department_member (int|None): ID сотрудника отдела.
        created_at (str): Дата создания.
        chat_id (int): ID чата.
        history (list): История изменений.
        group_messages (list): Групповые сообщения.
        private_messages (list): Приватные сообщения.
        assistant_message_id (int|None): ID сообщения ассистенту.
        department_message_id (int|None): ID сообщения отделу.
        notification_message_id (int|None): ID уведомления.
    """
    id: int
    text: str
    media: Optional[list] = None  # теперь список медиа-объектов
    status: str = TASK_STATUS_NEW
    author_id: int = 0
    author_name: str = ""
    assistant_id: Optional[int] = None
    assistant_name: Optional[str] = None
    department: Optional[str] = None
    department_member: Optional[int] = None
    created_at: str = ""
    chat_id: int = 0
    history: list = field(default_factory=list)
    group_messages: list = field(default_factory=list)
    private_messages: list = field(default_factory=list)
    assistant_message_id: Optional[int] = None
    department_message_id: Optional[int] = None
    notification_message_id: Optional[int] = None


tasks: List[Dict[str, Any]] = []
"""
Глобальный список задач. Каждый элемент — словарь с данными задачи.
"""

def load_tasks() -> None:
    """
    Загружает задачи из JSON-файла в глобальный список tasks.
    Если файл не найден — tasks будет пустым.
    """
    global tasks
    
    logging.info(f"[DEBUG] load_tasks: file_path={TASKS_FILE}")
    
    try:
        with open(TASKS_FILE, "r") as f:
            tasks = json.load(f)
        # Миграция старого статуса 'активно' в 'новая'
        changed = False
        for t in tasks:
            if t.get("status") == TASK_STATUS_ACTIVE:
                t["status"] = TASK_STATUS_NEW
                changed = True
        if changed:
            save_tasks()
    except FileNotFoundError:
        tasks = []
    except Exception as e:
        logging.error(f"Ошибка загрузки задач: {e}")
        tasks = []

def notify_director_critical_loss(bot, prev_count, new_count):
    try:
        text = (
            f"❗️ Критическая ошибка: попытка сохранить слишком мало задач!\n"
            f"Было: {prev_count}, стало: {new_count}.\n"
            f"Операция отменена для предотвращения потери данных."
        )
        bot.send_message(chat_id=GENERAL_DIRECTOR_ID, text=text)
    except Exception as e:
        logging.error(f"Не удалось уведомить директора о критической ошибке: {e}")

def save_tasks(bot=None) -> None:
    """
    Сохраняет список задач в JSON файл.
    
    Args:
        bot: Объект бота для уведомлений (опционально)
    """
    global tasks
    
    prev_count = len(tasks)
    
    # Убираем автоматическое удаление завершенных задач
    # Теперь задачи удаляются только через cleanup_finished_tasks() через 7 дней
    
    # Проверка на критическую потерю данных
    if prev_count > 10 and len(tasks) < prev_count * 0.5:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: попытка сохранить слишком мало задач! Было: {prev_count}, стало: {len(tasks)}")
        if bot:
            notify_director_critical_loss(bot, prev_count, len(tasks))
        return
    
    logging.info(f"[DEBUG] save_tasks: file_path={TASKS_FILE}, всего задач={len(tasks)}")
    
    try:
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения задач: {e}")
        if bot:
            try:
                bot.send_message(
                    chat_id=GENERAL_DIRECTOR_ID,
                    text=f"❌ Ошибка сохранения задач: {e}"
                )
            except:
                pass

def set_old_tasks_in_progress() -> None:
    """
    Устанавливает статус 'в работе' для старых задач со статусом 'новая'.
    """
    global tasks
    
    changed = False
    for task in tasks:
        if task.get("status") == TASK_STATUS_NEW:
            task["status"] = TASK_STATUS_IN_PROGRESS
            changed = True
    
    if changed:
        save_tasks()

def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    """
    Возвращает задачу по её ID.
    
    Args:
        task_id (int): ID задачи
        
    Returns:
        Optional[Dict[str, Any]]: Задача или None, если не найдена
    """
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None

def add_or_update_task(task: dict):
    """
    Добавляет новую задачу или обновляет существующую.
    
    Args:
        task (dict): Словарь с данными задачи
        
    Returns:
        dict: Обновленная задача
    """
    load_tasks()
    
    # Ищем существующую задачу
    existing_task = None
    for i, t in enumerate(tasks):
        if t.get("id") == task.get("id"):
            existing_task = i
            break
    
    if existing_task is not None:
        # Обновляем существующую задачу
        tasks[existing_task].update(task)
        updated_task = tasks[existing_task]
    else:
        # Добавляем новую задачу
        tasks.append(task)
        updated_task = task
    
    save_tasks()
    return updated_task

def get_tasks() -> list:
    """
    Возвращает список всех задач.
    
    Returns:
        list: Список всех задач
    """
    load_tasks()
    return tasks

def cleanup_finished_tasks() -> int:
    """
    Удаляет завершенные и отмененные задачи, которые старше недели.
    
    Returns:
        int: Количество удаленных задач
    """
    global tasks
    
    load_tasks()
    
    from datetime import datetime, timedelta
    
    initial_count = len(tasks)
    tasks_to_remove = []
    week_ago = datetime.now() - timedelta(days=7)
    
    for i, task in enumerate(tasks):
        status = task.get("status", "")
        if status in [TASK_STATUS_FINISHED, TASK_STATUS_CANCELLED]:
            # Проверяем, когда задача была завершена/отменена
            created_at = task.get("created_at", "")
            if created_at:
                try:
                    # Парсим дату создания
                    task_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    # Если задача старше недели - удаляем
                    if task_date < week_ago:
                        tasks_to_remove.append(i)
                except Exception as e:
                    logging.error(f"Ошибка парсинга даты для задачи {task.get('id')}: {e}")
                    # Если не можем распарсить дату, удаляем задачу старше недели по ID
                    task_id = task.get('id', 0)
                    if task_id > 0:
                        # Примерно вычисляем дату по ID (ID содержит timestamp)
                        task_timestamp = task_id / 1000  # конвертируем в секунды
                        task_date = datetime.fromtimestamp(task_timestamp)
                        if task_date < week_ago:
                            tasks_to_remove.append(i)
    
    # Удаляем задачи в обратном порядке
    for i in reversed(tasks_to_remove):
        removed_task = tasks.pop(i)
        logging.info(f"Очистка: удалена задача ID {removed_task.get('id')} со статусом '{removed_task.get('status')}' (старше недели)")
    
    removed_count = initial_count - len(tasks)
    
    if removed_count > 0:
        save_tasks()
        logging.info(f"Очистка завершена: удалено {removed_count} задач старше недели")
    
    return removed_count
