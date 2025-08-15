import datetime
from typing import Dict, Any, List

def format_task_message(task: Dict[str, Any]) -> str:
    text = task.get('text', '')
    assistant = task.get('assistant_name', 'не назначен')
    author = task.get('author_name', 'неизвестно')
    status = task.get('status', 'неизвестно').capitalize()
    dep_key = task.get('department')
    try:
        from services_veretevo import department_service
        dep_name = department_service.DEPARTMENTS.get(dep_key, {}).get('name', dep_key or '—')
    except Exception:
        dep_name = dep_key or '—'
    try:
        created = datetime.datetime.fromisoformat(task.get('created_at', ''))
        created = created.strftime("%d.%m.%Y %H:%M")
    except Exception:
        created = task.get('created_at', '')
    msg = f"📝 <b>Задача:</b> {text or '(без текста)'}\n"
    msg += f"<b>Отдел:</b> {dep_name}\n"
    msg += f"<b>Ответственный:</b> {assistant}\n"
    msg += f"<b>Поставил:</b> {author}\n"
    msg += f"<b>Создано:</b> {created}\n\n"
    if status == 'Новая':
        msg += f"🚩 <b>НОВАЯ ЗАДАЧА</b>"
    elif status == 'В работе':
        msg += f"🛠️ <b>В РАБОТЕ</b>"
    elif status == 'Завершено':
        msg += f"✅ <b>ЗАВЕРШЕНО</b>"
    elif status == 'Отменено':
        msg += f"❌ <b>ОТМЕНЕНО</b>"
    else:
        msg += f"📊 <b>Статус:</b> {status}"
    return msg

def build_tasks_report(tasks: List[Dict[str, Any]], title: str = "Отчёт по задачам") -> str:
    if not tasks:
        return f"{title}\nНет задач."
    lines = [f"{title}"]
    for t in tasks:
        lines.append(format_task_message(t))
        lines.append("------")
    return "\n".join(lines)
