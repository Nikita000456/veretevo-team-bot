import logging
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from typing import Any, Dict, Optional

def main_menu_keyboard(chat_type: str = "private", user_id: Optional[int] = None) -> ReplyKeyboardMarkup | None:
    logging.debug(f"main_menu_keyboard вызван для chat_type={chat_type}, user_id={user_id}")
    if chat_type != "private":
        return None
    buttons = [["📌 Новая задача", "📋 Список задач"], ["Мои задачи"]]
    # Кнопка 'Помощь' полностью убрана для всех пользователей
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_task_action_keyboard(task: Dict[str, Any], user_id: Optional[int], department_members: Optional[list] = None) -> InlineKeyboardMarkup | None:
    from config_veretevo.constants import GENERAL_DIRECTOR_ID
    status = task.get('status')
    author_id = task.get('author_id')
    assistant_id = task.get('assistant_id')
    buttons = []
    
    logging.info(f"🎯 get_task_action_keyboard: status={status}, user_id={user_id}, author_id={author_id}, assistant_id={assistant_id}")
    
    # Если задача завершена или отменена, НЕ показываем кнопки вообще
    if status in ['завершено', 'отменено']:
        logging.info(f"🎯 Задача {status}, кнопки не показываем")
        return None
    
    # Если user_id не передан (группа) — показываем кнопки по статусу задачи
    if user_id is None:
        if status == 'новая':
            buttons.append(InlineKeyboardButton("Взять в работу", callback_data=f"take_{task.get('id','')}") )
        # Кнопки "Завершить" и "Отменить" показываем для всех в групповом чате
        if status in ['новая', 'в работе']:
            buttons.append(InlineKeyboardButton("✅ Завершить", callback_data=f"finish_{task.get('id','')}") )
            buttons.append(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{task.get('id','')}") )
        logging.info(f"🎯 Групповой чат, статус {status}, кнопки: {[btn.text for btn in buttons]}")
        return InlineKeyboardMarkup([buttons])
    
    # Проверяем права доступа пользователя
    is_director = user_id == GENERAL_DIRECTOR_ID
    is_author = user_id == author_id
    is_assistant = user_id == assistant_id
    is_department_member = False
    if department_members is not None:
        is_department_member = str(user_id) in department_members
    
    logging.info(f"🎯 Права доступа: is_director={is_director}, is_author={is_author}, is_assistant={is_assistant}, is_department_member={is_department_member}")
    
    # "Взять в работу" — если задача новая и пользователь — член отдела или директор
    if status == 'новая':
        if is_director or is_department_member:
            buttons.append(InlineKeyboardButton("Взять в работу", callback_data=f"take_{task.get('id','')}") )
    
    # "Завершить" — показывается для всех и работает для всех, если задача активна
    if status in ['новая', 'в работе']:
        buttons.append(InlineKeyboardButton("✅ Завершить", callback_data=f"finish_{task.get('id','')}") )
    
    # "Отменить" — показывается для всех, но работает только для автора или директора
    if status in ['новая', 'в работе']:
        buttons.append(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{task.get('id','')}") )
    
    logging.info(f"🎯 Итоговые кнопки для пользователя {user_id}: {[btn.text for btn in buttons]}")
    return InlineKeyboardMarkup([buttons])
