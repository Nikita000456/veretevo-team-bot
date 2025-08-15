import os

# Версия проекта
VERSION = "2.1.0"

GENERAL_DIRECTOR_ID = 406325177

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_FILE = os.path.join(BASE_DIR, "data/tasks.json")
DEPARTMENTS_JSON_PATH = os.path.join(BASE_DIR, "config_veretevo", "departments_config.json")
AUDIT_LOG_PATH = os.path.join(BASE_DIR, "logs", "audit.log")

# Статусы задач
TASK_STATUS_NEW = "новая"
TASK_STATUS_ACTIVE = "активно"
TASK_STATUS_IN_PROGRESS = "в работе"
TASK_STATUS_FINISHED = "завершено"
TASK_STATUS_CANCELLED = "отменено"

TASK_STATUSES = [
    TASK_STATUS_NEW,
    TASK_STATUS_ACTIVE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_FINISHED,
    TASK_STATUS_CANCELLED,
]
