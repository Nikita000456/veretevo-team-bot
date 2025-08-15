import logging
from services_veretevo.department_service import DEPARTMENTS
import services_veretevo.task_service as task_service
from utils_veretevo.formatting import build_tasks_report

async def send_morning_report(bot):
    task_service.load_tasks()
    for dep_key, dep in DEPARTMENTS.items():
        dep_chat_id = dep.get("chat_id")
        if not dep_chat_id:
            continue
        morning_tasks = [
            t for t in task_service.tasks 
            if t.get("status") in ("новая", "в работе") and t.get("department") == dep_key
        ]
        # Отправляем уведомление только если есть задачи
        if morning_tasks:
            report = build_tasks_report(morning_tasks, f"Планы на день — {dep['name']}")
            await bot.send_message(dep_chat_id, report, parse_mode="HTML")

async def send_evening_report(bot):
    task_service.load_tasks()
    for dep_key, dep in DEPARTMENTS.items():
        dep_chat_id = dep.get("chat_id")
        if not dep_chat_id:
            continue
        open_tasks = [
            t for t in task_service.tasks 
            if t.get("status") not in ("завершено", "отменено") and t.get("department") == dep_key
        ]
        # Отправляем уведомление только если есть задачи
        if open_tasks:
            report = build_tasks_report(open_tasks, f"Невыполнённые задачи — {dep['name']}")
            await bot.send_message(dep_chat_id, report, parse_mode="HTML")

def register_report_handlers(application):
    pass  # Отчёты вызываются по расписанию, не через команды
