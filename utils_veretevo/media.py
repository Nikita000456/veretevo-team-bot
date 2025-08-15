import logging
from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Any, Dict, Optional
from utils_veretevo.formatting import format_task_message
from config_veretevo.env import ASSISTANTS_CHAT_ID, FINANCE_CHAT_ID
from services_veretevo.department_service import DEPARTMENTS
from utils_veretevo.keyboards import get_task_action_keyboard
from utils_veretevo.todoist_service import add_comment

async def send_task_with_media(context: ContextTypes.DEFAULT_TYPE, chat_id: int, task: Dict[str, Any], reply_markup: Optional[InlineKeyboardMarkup] = None):
    logging.debug(f"send_task_with_media: task_id={task.get('id')}, chat_id={chat_id}")
    media_list = task.get("media")
    text = task.get("text", "")
    assistant = task.get('assistant_name', 'не назначен')
    author = task.get('author_name', 'неизвестно')
    status = task.get('status', 'неизвестно').capitalize()
    try:
        created = task.get('created_at', '')
    except Exception:
        created = task.get('created_at', '')
    info = format_task_message(task)
    if media_list:
        try:
            from telegram import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument
            # Если это список и больше одного медиа — отправляем как альбом
            if isinstance(media_list, list) and len(media_list) > 1:
                media_group = []
                for idx, m in enumerate(media_list):
                    if m["type"] == "photo":
                        media_group.append(InputMediaPhoto(media=m["file_id"], caption=info if idx == 0 else None, parse_mode="HTML" if idx == 0 else None))
                    elif m["type"] == "video":
                        media_group.append(InputMediaVideo(media=m["file_id"], caption=info if idx == 0 else None, parse_mode="HTML" if idx == 0 else None))
                    elif m["type"] == "audio":
                        media_group.append(InputMediaAudio(media=m["file_id"], caption=info if idx == 0 else None, parse_mode="HTML" if idx == 0 else None))
                    elif m["type"] == "document":
                        media_group.append(InputMediaDocument(media=m["file_id"], caption=info if idx == 0 else None, parse_mode="HTML" if idx == 0 else None))
                msgs = await context.bot.send_media_group(chat_id, media_group)
                # Отдельно отправляем кнопки (reply_markup) после альбома
                if reply_markup:
                    await context.bot.send_message(chat_id, "⬆️ К задаче прикреплены файлы. Действия:", reply_markup=reply_markup)
                return msgs[0] if msgs else None
            # Если только один медиа-объект — как раньше
            media = media_list[0] if isinstance(media_list, list) else media_list
            if media["type"] == "photo":
                return await context.bot.send_photo(chat_id, media["file_id"], caption=info, reply_markup=reply_markup, parse_mode="HTML")
            elif media["type"] == "video":
                return await context.bot.send_video(chat_id, media["file_id"], caption=info, reply_markup=reply_markup, parse_mode="HTML")
            elif media["type"] == "audio":
                return await context.bot.send_audio(chat_id, media["file_id"], caption=info, reply_markup=reply_markup, parse_mode="HTML")
            elif media["type"] == "voice":
                return await context.bot.send_voice(chat_id, media["file_id"], caption=info, reply_markup=reply_markup, parse_mode="HTML")
        except Exception as e:
            logging.debug(f"[ERROR] Не удалось отправить медиа: {e}")
            # Явное уведомление пользователю
            try:
                await context.bot.send_message(chat_id, "❗ Не удалось отправить медиафайл (фото/видео/аудио/войс). Проверьте формат и повторите попытку.")
            except Exception as e2:
                logging.error(f"[ERROR] Не удалось отправить уведомление об ошибке медиа: {e2}")
            return await context.bot.send_message(chat_id, info, reply_markup=reply_markup, parse_mode="HTML")
    return await context.bot.send_message(chat_id, info, reply_markup=reply_markup, parse_mode="HTML")

async def update_task_messages(context: ContextTypes.DEFAULT_TYPE, task_id: int, new_status: str):
    from services_veretevo.task_service import get_task_by_id
    task = get_task_by_id(task_id)
    if not task:
        return
    logging.debug(f"Обновляем сообщения для задачи {task_id}, статус: {new_status}")
    messages_to_update = []
    if "group_messages" in task:
        messages_to_update.extend(task["group_messages"])
    if "private_messages" in task:
        messages_to_update.extend(task["private_messages"])
    if task.get("assistant_message_id"):
        messages_to_update.append({
            "chat_id": ASSISTANTS_CHAT_ID,
            "message_id": task["assistant_message_id"]
        })
    if task.get("department_message_id"):
        for dep_key, dep in DEPARTMENTS.items():
            if dep.get("chat_id"):
                messages_to_update.append({
                    "chat_id": dep["chat_id"],
                    "message_id": task["department_message_id"]
                })
                break
    for msg_info in messages_to_update:
        try:
            # Определяем user_id для inline-кнопок: для групповых сообщений None, для личных — id пользователя
            user_id = None
            if "chat_id" in msg_info and str(msg_info["chat_id"]).startswith("-100"):  # supergroup/group
                user_id = None
            elif "chat_id" in msg_info:
                user_id = task.get("assistant_id")  # для личных сообщений можно использовать ответственного
            keyboard = get_task_action_keyboard(task, user_id)
            if task.get('media') and isinstance(task['media'], list) and len(task['media']) > 1:
                # Альбом: обновляем только caption первого сообщения
                try:
                    await context.bot.edit_message_caption(
                        chat_id=msg_info["chat_id"],
                        message_id=msg_info["message_id"],
                        caption=format_task_message(task),
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logging.debug(f"Ошибка обновления caption альбома: {e}")
            elif task.get('media') and (isinstance(task['media'], list) or isinstance(task['media'], dict)) and (task['media'][0]['type'] in ['photo', 'video', 'audio', 'voice'] if isinstance(task['media'], list) else task['media']['type'] in ['photo', 'video', 'audio', 'voice']):
                await context.bot.edit_message_caption(
                    chat_id=msg_info["chat_id"],
                    message_id=msg_info["message_id"],
                    caption=format_task_message(task),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=msg_info["chat_id"],
                    message_id=msg_info["message_id"],
                    text=format_task_message(task),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.debug(f"Ошибка обновления сообщения в чате {msg_info['chat_id']}: {e}")

async def send_task_action_comment(context: ContextTypes.DEFAULT_TYPE, task: dict, action: str, user_id: int):
    """
    Отправляет стандартизированный комментарий в группу/отдел о действии с задачей.
    action: 'take', 'finish', 'cancel'
    """
    from config_veretevo.env import ASSISTANTS_CHAT_ID
    from services_veretevo.department_service import DEPARTMENTS
    # Новый способ: всегда имя того, кто совершил действие
    def get_user_name(user_id):
        for dep in DEPARTMENTS.values():
            if str(user_id) in dep.get("members", {}):
                return dep["members"][str(user_id)]
        return "Пользователь"
    user_name = get_user_name(user_id)
    task_title = task.get('text', 'Без названия')
    dep_key = task.get('department')
    dep_chat_id = None
    if dep_key and dep_key in DEPARTMENTS:
        dep_chat_id = DEPARTMENTS[dep_key].get('chat_id')
    if not dep_chat_id:
        dep_chat_id = ASSISTANTS_CHAT_ID
    if action == 'take':
        msg = f"🟡 {user_name} взял(а) задачу «{task_title}» в работу"
    elif action == 'finish':
        msg = f"✅ {user_name} завершил(а) задачу «{task_title}»"
    elif action == 'cancel':
        msg = f"❌ {user_name} отменил(а) задачу «{task_title}»"
    else:
        msg = f"ℹ️ {user_name} выполнил(а) действие с задачей «{task_title}»"
    try:
        await context.bot.send_message(dep_chat_id, msg)
    except Exception as e:
        import logging
        logging.error(f"Не удалось отправить комментарий в чат {dep_chat_id}: {e}")
    # --- Синхронизация комментария с Todoist ---
    if task.get("todoist_task_id"):
        try:
            add_comment(task["todoist_task_id"], msg)
        except Exception as e:
            import logging
            logging.error(f"[TODOIST] Не удалось добавить комментарий в Todoist: {e}")
    # --- Конец синхронизации ---
