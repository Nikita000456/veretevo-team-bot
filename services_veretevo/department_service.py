"""
Модуль для работы с отделами. Содержит функции загрузки, сохранения, миграции и поиска отделов.
"""
import json
from typing import Dict, Any, List, Tuple
from config_veretevo.constants import DEPARTMENTS_JSON_PATH, GENERAL_DIRECTOR_ID

DEPARTMENTS: Dict[str, Any] = {}
"""
Глобальный словарь с отделами. Ключ — строка (имя отдела), значение — словарь с данными отдела.
"""


def load_departments() -> None:
    """
    Загружает отделы из JSON-файла в глобальный словарь DEPARTMENTS.
    Если файл не найден или повреждён — DEPARTMENTS будет пустым.
    """
    import logging
    global DEPARTMENTS
    logging.info(f"[DEBUG] load_departments: пытаемся загрузить из {DEPARTMENTS_JSON_PATH}")
    try:
        with open(DEPARTMENTS_JSON_PATH, 'r', encoding='utf-8') as f:
            loaded_departments = json.load(f)
            DEPARTMENTS.clear()
            DEPARTMENTS.update(loaded_departments)
        logging.info(f"[DEBUG] load_departments: успешно загружено {len(DEPARTMENTS)} отделов")
        logging.info(f"[DEBUG] load_departments: отделы = {list(DEPARTMENTS.keys())}")
    except FileNotFoundError:
        logging.error(f"Ошибка загрузки departments_config.json: файл не найден: {DEPARTMENTS_JSON_PATH}")
        DEPARTMENTS.clear()
    except Exception as e:
        logging.error(f'Ошибка загрузки departments_config.json: {e}')
        DEPARTMENTS.clear()

def save_departments() -> None:
    """
    Сохраняет текущий глобальный словарь DEPARTMENTS в JSON-файл.
    """
    try:
        with open(DEPARTMENTS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEPARTMENTS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        import logging
        logging.error(f'Ошибка сохранения departments_config.json: {e}')

def migrate_departments_to_json(assistants, finance_members, assistants_chat_id, finance_chat_id) -> None:
    """
    Мигрирует старую структуру отделов в новый JSON-файл, если он ещё не существует или пустой.
    Используется для первичной инициализации.
    """
    import os
    if os.path.exists(DEPARTMENTS_JSON_PATH):
        try:
            with open(DEPARTMENTS_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data:
                return
        except Exception:
            pass
    departments = {
        "assistants": {
            "name": "Ассистенты",
            "chat_id": assistants_chat_id,
            "members": {str(k): v for k, v in assistants.items()}
        },
        "carpenters": {"name": "Плотники", "chat_id": None, "members": {}},
        "maintenance": {"name": "Эксплуатация", "chat_id": None, "members": {}},
        "tech": {"name": "Тех команда", "chat_id": None, "members": {}},
        "maids": {"name": "Горничные", "chat_id": None, "members": {}},
        "reception": {"name": "Ресепшен", "chat_id": None, "members": {}},
        "security": {"name": "Охрана", "chat_id": None, "members": {}},
        "finance": {
            "name": "Финансы",
            "chat_id": finance_chat_id,
            "members": {str(k): v for k, v in finance_members.items()}
        }
    }
    with open(DEPARTMENTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(departments, f, ensure_ascii=False, indent=2)

def get_user_departments(user_id: int) -> List[Tuple[str, str]]:
    """
    Возвращает список отделов, в которых состоит пользователь.

    Args:
        user_id (int): ID пользователя.

    Returns:
        List[Tuple[str, str]]: Список кортежей (ключ отдела, название отдела).
    """
    # Убеждаемся, что отделы загружены
    load_departments()
    user_deps = []
    user_id_str = str(user_id)
    for key, dep in DEPARTMENTS.items():
        if user_id_str in dep.get("members", {}):
            user_deps.append((key, dep["name"]))
    return user_deps
