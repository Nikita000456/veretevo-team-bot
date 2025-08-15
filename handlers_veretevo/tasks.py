import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, Application, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
import services_veretevo.department_service as department_service
from services_veretevo.department_service import DEPARTMENTS
from utils_veretevo.keyboards import main_menu_keyboard
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from services_veretevo.task_service import tasks, save_tasks, get_task_by_id, add_or_update_task
from utils_veretevo.keyboards import get_task_action_keyboard
from utils_veretevo.todoist_sync_polling import force_update_task_messages
from utils_veretevo.media import send_task_with_media, update_task_messages, send_task_action_comment
import datetime
from utils_veretevo.formatting import format_task_message
from utils_veretevo.todoist_service import close_task, delete_task
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber
import tempfile
import os
import re
from utils_veretevo.yandex_gpt import improve_task_text

# Инициализируем Yandex SpeechKit транскрайбер
try:
    voice_transcriber = YandexSpeechKitTranscriber()
    print("[INFO] Yandex SpeechKit транскрайбер инициализирован успешно")
except Exception as e:
    print(f"[ОШИБКА] Не удалось инициализировать Yandex SpeechKit: {e}")
    voice_transcriber = None

# Состояния ConversationHandler
WAITING_FOR_TASK_TEXT = 1
WAITING_FOR_ASSIGN_TYPE = 2
WAITING_FOR_DEPARTMENT_MEMBER = 3
WAITING_FOR_ASSISTANT_CHOICE = 4

# --- Создание задачи ---
async def new_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запускает процесс создания новой задачи для пользователя.
    Проверяет, состоит ли пользователь в отделе, и предлагает выбрать отдел или ввести текст задачи.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    logging.debug("new_task_start вызван")
    department_service.load_departments()
    user_id = update.effective_user.id if update.effective_user else None
    logging.info(f"[DEBUG] new_task_start: user_id={user_id}")
    user_deps = department_service.get_user_departments(user_id) if user_id else None
    logging.info(f"[DEBUG] new_task_start: get_user_departments({user_id}) => {user_deps}")
    logging.info(f"[DEBUG] new_task_start: DEPARTMENTS keys = {list(DEPARTMENTS.keys())}")
    logging.info(f"[DEBUG] new_task_start: DEPARTMENTS content = {DEPARTMENTS}")
    if not user_id:
        await update.message.reply_text("Ошибка: не удалось определить пользователя.")
        return
    if not user_deps:
        await update.message.reply_text("Вы не состоите ни в одном отделе и не можете ставить задачи.")
        return
    if len(user_deps) == 1:
        dep_key, dep_name = user_deps[0]
        if context.user_data is None:
            context.user_data = {}
        context.user_data['department'] = dep_key
        # Меню только с одной кнопкой 'Отмена'
        cancel_keyboard = ReplyKeyboardMarkup(
            [["❌ Отмена"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text(f"Введите текст задачи для отдела: {dep_name}", reply_markup=cancel_keyboard)
        context.user_data['creating_task'] = True
        return WAITING_FOR_TASK_TEXT
    # Если отделов несколько — предлагаем выбрать
    keyboard = [[InlineKeyboardButton(dep_name, callback_data=f"choose_dep_create_{dep_key}")] for dep_key, dep_name in user_deps]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_task")])
    
    # Добавляем логирование для отладки
    logging.info(f"[DEBUG] new_task_start: созданные callback_data для кнопок:")
    for dep_key, dep_name in user_deps:
        callback_data = f"choose_dep_create_{dep_key}"
        logging.info(f"[DEBUG] new_task_start: {dep_name} -> {callback_data}")
    
    await update.message.reply_text(
        "В какой отдел поставить задачу?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_FOR_DEPARTMENT_MEMBER

async def choose_department_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор отдела для создания задачи через callback-кнопку.
    Проверяет доступ пользователя к отделу и предлагает ввести текст задачи.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    # Добавляем логирование для отладки ДО загрузки отделов
    from services_veretevo.department_service import DEPARTMENTS
    logging.info(f"[DEBUG] choose_department_create_callback: DEPARTMENTS ДО load_departments() = {list(DEPARTMENTS.keys())}")
    
    department_service.load_departments()
    
    # Добавляем логирование для отладки ПОСЛЕ загрузки отделов
    logging.info(f"[DEBUG] choose_department_create_callback: DEPARTMENTS ПОСЛЕ load_departments() = {list(DEPARTMENTS.keys())}")
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await query.message.reply_text("Ошибка: не удалось определить пользователя.")
        return
    data = query.data
    logging.info(f"[DEBUG] choose_department_create_callback: callback_data={data}")
    if data == "cancel_create_task":
        # Удаляем сообщение с кнопками
        try:
            await query.message.delete()
        except Exception as e:
            logging.debug(f"Ошибка удаления сообщения при отмене: {e}")
        
        chat_type = update.effective_chat.type if update.effective_chat else "private"
        user_id = update.effective_user.id if update.effective_user else None
        reply_markup = main_menu_keyboard(chat_type, user_id)
        await query.message.reply_text("Создание задачи отменено.", reply_markup=reply_markup)
        return ConversationHandler.END
    if data.startswith("choose_dep_create_"):
        dep_key = data[len("choose_dep_create_"):]
        # Получаем актуальные отделы напрямую из модуля, как в new_task_start
        from services_veretevo.department_service import DEPARTMENTS
        logging.info(f"[DEBUG] dep_key={dep_key}, DEPARTMENTS keys={list(DEPARTMENTS.keys())}")
        logging.info(f"[DEBUG] DEPARTMENTS content: {DEPARTMENTS}")
        logging.info(f"[DEBUG] dep_key in DEPARTMENTS: {dep_key in DEPARTMENTS}")
        if dep_key not in DEPARTMENTS:
            logging.error(f"[ERROR] Отдел '{dep_key}' не найден в DEPARTMENTS!")
            await query.message.reply_text("Ошибка: отдел не найден.")
            return
        dep = DEPARTMENTS.get(dep_key)
        user_id_str = str(user_id)
        if not dep or (user_id_str not in dep.get("members", {}) and user_id != GENERAL_DIRECTOR_ID):
            await query.message.reply_text("У вас нет доступа к этому отделу.")
            return
        if context.user_data is None:
            context.user_data = {}
        context.user_data['department'] = dep_key
        logging.info(f"[DEBUG] choose_department_create_callback: сохранен отдел '{dep_key}' в context.user_data")
        # Меню только с одной кнопкой 'Отмена'
        cancel_keyboard = ReplyKeyboardMarkup(
            [["❌ Отмена"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logging.debug(f"Ошибка очистки клавиатуры выбора отдела: {e}")
        await query.message.reply_text(f"Введите текст задачи для отдела: {dep['name']}", reply_markup=cancel_keyboard)
        context.user_data['creating_task'] = True
        return WAITING_FOR_TASK_TEXT

async def receive_task_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получает текст задачи (или медиа) от пользователя, формирует клавиатуру выбора исполнителя.
    Если пользователь отменяет — завершает процесс создания задачи.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    text = update.message.text
    # Универсальная обработка: фото, документ, видео, аудио, текст
    media = None
    text_val = None
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logging.info(f"[SMART] receive_task_text: user_id={user_id}, text='{update.message.text}', photo={bool(update.message.photo)}, document={bool(update.message.document)}")
    if text == "❌ Отмена":
        if context.user_data:
            context.user_data.pop('creating_task', None)
            context.user_data.pop('task_text', None)
            context.user_data.pop('media', None)
        chat_type = update.effective_chat.type if update.effective_chat else "private"
        reply_markup = main_menu_keyboard(chat_type, user_id)
        await update.message.reply_text("Создание задачи отменено.", reply_markup=reply_markup)
        return ConversationHandler.END
    if not context.user_data or not context.user_data.get('creating_task'):
        return
    dep_key = context.user_data.get('department')
    # --- Фото ---
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        media = {"type": "photo", "file_id": file_id}
        text_val = update.message.caption
        logging.info(f"[SMART] Получено фото: file_id={file_id}, caption='{text_val}'")
        if not text_val or not text_val.strip():
            # Нет подписи — просим ввести текст задачи
            context.user_data['media'] = media
            await update.message.reply_text("Пожалуйста, введите текст задачи для этого фото.")
            return WAITING_FOR_TASK_TEXT
    # --- Документ ---
    elif update.message.document:
        file_id = update.message.document.file_id
        media = {"type": "document", "file_id": file_id}
        logging.info(f"[SMART] Получен документ: file_id={file_id}, filename={update.message.document.file_name}")
        # У документов нет подписи — всегда просим текст задачи
        context.user_data['media'] = media
        await update.message.reply_text("Пожалуйста, введите текст задачи для этого документа.")
        return WAITING_FOR_TASK_TEXT
    # --- Видео ---
    elif update.message.video:
        file_id = update.message.video.file_id
        media = {"type": "video", "file_id": file_id}
        text_val = update.message.caption
        logging.info(f"[SMART] Получено видео: file_id={file_id}, caption='{text_val}'")
        if not text_val or not text_val.strip():
            context.user_data['media'] = media
            await update.message.reply_text("Пожалуйста, введите текст задачи для этого видео.")
            return WAITING_FOR_TASK_TEXT
    # --- Аудио ---
    elif update.message.audio:
        file_id = update.message.audio.file_id
        media = {"type": "audio", "file_id": file_id}
        text_val = update.message.caption
        logging.info(f"[SMART] Получено аудио: file_id={file_id}, caption='{text_val}'")
        if not text_val or not text_val.strip():
            context.user_data['media'] = media
            await update.message.reply_text("Пожалуйста, введите текст задачи для этого аудиофайла.")
            return WAITING_FOR_TASK_TEXT
    # --- Голосовое ---
    elif update.message.voice:
        file_id = update.message.voice.file_id
        media = {"type": "voice", "file_id": file_id}
        logging.info(f"[SMART] Получено voice: file_id={file_id}")
        context.user_data['media'] = media
        await update.message.reply_text("Пожалуйста, введите текст задачи для этого голосового сообщения.")
        return WAITING_FOR_TASK_TEXT
    # --- Текст ---
    else:
        text_val = update.message.text or ""
        logging.info(f"[SMART] Получен текст: '{text_val}'")
        # Если до этого было медиа — берём его из context.user_data['media']
        media = context.user_data.get('media')
        # После получения текста — показываем выбор ответственного
        if not text_val.strip():
            await update.message.reply_text("Пожалуйста, введите текст задачи.")
            return WAITING_FOR_TASK_TEXT
    # --- Показать клавиатуру выбора ответственного ---
    context.user_data['task_text'] = text_val
    context.user_data['media'] = media
    members = DEPARTMENTS.get(dep_key, {}).get("members", {}) if dep_key else {}
    keyboard = []
    
    # Для всех отделов: показываем всех, кроме себя и генерального директора
    current_user_id = str(update.effective_user.id) if update.effective_user else None
    for uid, name in members.items():
        if uid != current_user_id and uid != GENERAL_DIRECTOR_ID:  # Не показываем себя и генерального директора
            if dep_key == "assistants" and uid == GENERAL_DIRECTOR_ID:
                keyboard.append([InlineKeyboardButton(f"Генеральный директор: {name}", callback_data=f"assign_{uid}")])
            elif dep_key == "assistants":
                keyboard.append([InlineKeyboardButton(f"Ассистент: {name}", callback_data=f"assign_{uid}")])
            else:
                keyboard.append([InlineKeyboardButton(f"Сотрудник: {name}", callback_data=f"assign_{uid}")])
    
    keyboard.append([InlineKeyboardButton("Без назначения", callback_data="assign_none")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if dep_key == "assistants":
        await update.message.reply_text(
            "Кому назначить задачу? (Выберите ассистента, генерального директора или 'Без назначения')",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "Кому назначить задачу? (Выберите сотрудника или 'Без назначения')",
            reply_markup=reply_markup,
        )
    return WAITING_FOR_ASSIGN_TYPE

async def create_task_from_voice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает создание задачи из голосового сообщения.
    """
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        dep_key = data.replace("create_task_from_voice_", "")
        
        logging.info(f"[DEBUG] create_task_from_voice_callback вызван с data: '{data}', dep_key: '{dep_key}'")
        
        if dep_key not in DEPARTMENTS:
            logging.error(f"[DEBUG] Отдел не найден: '{dep_key}'")
            await query.message.reply_text("Ошибка: отдел не найден.")
            return
        
        # Получаем текст из предыдущего сообщения (транскрипции)
        message_text = query.message.text
        if "Распознанный текст:" in message_text:
            # Извлекаем текст из сообщения
            lines = message_text.split('\n')
            transcript_lines = []
            in_transcript = False
            for line in lines:
                if "Распознанный текст:" in line:
                    in_transcript = True
                    continue
                elif "Обнаружен отдел:" in line:
                    break
                elif in_transcript and line.strip():
                    transcript_lines.append(line.strip())
            
            if transcript_lines:
                task_text = ' '.join(transcript_lines)
                
                # Создаем задачу
                user_id = update.effective_user.id if update.effective_user else 0
                author_name = update.effective_user.full_name if update.effective_user else "Неизвестно"
                chat_id = update.effective_chat.id if update.effective_chat else 0
                
                task = {
                    "id": int(datetime.datetime.now().timestamp() * 1000),
                    "text": task_text,
                    "media": None,
                    "status": "новая",
                    "author_id": user_id,
                    "author_name": author_name,
                    "assistant_id": None,
                    "assistant_name": None,
                    "department": dep_key,
                    "department_member": None,
                    "created_at": datetime.datetime.now().isoformat(),
                    "chat_id": chat_id,
                    "history": []
                }
                
                from services_veretevo.task_service import add_or_update_task
                add_or_update_task(task)
                
                # Отправляем задачу в чат отдела
                dep_chat_id = DEPARTMENTS[dep_key].get('chat_id')
                dep_name = DEPARTMENTS[dep_key].get('name', 'Неизвестно')
                
                if dep_chat_id:
                    from utils_veretevo.keyboards import get_task_action_keyboard
                    from utils_veretevo.media import send_task_with_media
                    task_keyboard = get_task_action_keyboard(task, None)
                    sent_msg = await send_task_with_media(context, dep_chat_id, task, reply_markup=task_keyboard)
                    if sent_msg:
                        if "group_messages" not in task:
                            task["group_messages"] = []
                        task["group_messages"].append({
                            "chat_id": dep_chat_id,
                            "message_id": sent_msg.message_id
                        })
                        add_or_update_task(task)
                
                # Отправляем подтверждение пользователю
                chat_type = update.effective_chat.type if update.effective_chat else "private"
                reply_markup = main_menu_keyboard(chat_type, user_id)
                await query.message.reply_text(
                    f"✅ Задача создана и отправлена в отдел: {dep_name}\n\nТекст задачи:\n{task_text}",
                    reply_markup=reply_markup
                )
                
                # Удаляем сообщение с кнопкой
                try:
                    await query.message.delete()
                except Exception as e:
                    logging.debug(f"Ошибка удаления сообщения: {e}")
            else:
                await query.message.reply_text("Ошибка: не удалось извлечь текст задачи.")
        else:
            await query.message.reply_text("Ошибка: не найден текст задачи.")
    except Exception as e:
        logging.error(f"Ошибка в create_task_from_voice_callback: {e}")
        await query.message.reply_text("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")

async def assign_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор типа назначения задачи (ассистент или сотрудник отдела) через callback-кнопку.
    В зависимости от отдела вызывает соответствующий обработчик.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    query = update.callback_query
    data = query.data
    if data == "cancel_task":
        return await cancel_task_callback(update, context)
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    dep_key = context.user_data.get('department') if context.user_data else None
    if data.startswith("assign_") or data == "assign_none":
        if dep_key == "assistants":
            return await assign_assistant(update, context)
        else:
            return await assign_department(update, context)

async def assign_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает назначение задачи сотруднику отдела или всем сотрудникам отдела.
    Сохраняет задачу, отправляет её в чат отдела, очищает временные данные пользователя.
    """
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    data = query.data
    if data == "cancel_task":
        return await cancel_task_callback(update, context)
    if context.user_data is None:
        context.user_data = {}
    dep_key = context.user_data.get('department')
    # Получаем актуальные отделы напрямую из модуля
    from services_veretevo.department_service import DEPARTMENTS
    dep_members = DEPARTMENTS.get(dep_key, {}).get("members", {}) if dep_key else {}
    dep_member = None
    assistant_id = None
    assistant_name = None
    if data.startswith("assign_"):
        if data == "assign_none":
            dep_member = None
            assistant_id = None
            assistant_name = "Без назначения"
        else:
            try:
                dep_member = int(data.split("_", 1)[1])
                # Проверка: выбранный сотрудник должен быть в отделе
                if str(dep_member) not in dep_members:
                    await query.message.reply_text("Ошибка: выбранный сотрудник не состоит в этом отделе.")
                    return ConversationHandler.END
                assistant_id = dep_member
                assistant_name = dep_members.get(str(dep_member), "Неизвестно")
            except ValueError:
                await query.message.reply_text("Ошибка: неверный ID сотрудника.")
                return ConversationHandler.END
        context.user_data['department_member'] = dep_member
    user_id = update.effective_user.id if update.effective_user else 0
    author_name = update.effective_user.full_name if update.effective_user else "Неизвестно"
    chat_id = update.effective_chat.id if update.effective_chat else 0
    task = {
        "id": int(datetime.datetime.now().timestamp() * 1000),
        "text": context.user_data.get('task_text', ""),
        "media": context.user_data.get('media') if context.user_data.get('media') else None,
        "status": "новая",
        "author_id": user_id,
        "author_name": author_name,
        "assistant_id": assistant_id,
        "assistant_name": assistant_name,
        "department": dep_key,
        "department_member": dep_member,
        "created_at": datetime.datetime.now().isoformat(),
        "chat_id": chat_id,
        "history": []
    }
    # --- Добавлено: создание задачи в Todoist для генерального директора ---
    from config_veretevo.constants import GENERAL_DIRECTOR_ID
    if assistant_id == GENERAL_DIRECTOR_ID:
        try:
            from utils_veretevo.todoist_service import create_task
            todoist_id = create_task(
                content=task["text"],
                description=f"Поставил: {author_name} (id: {user_id})"
            )
            task["todoist_task_id"] = todoist_id
        except Exception as e:
            logging.error(f"[TODOIST] Ошибка создания задачи в Todoist: {e}")
    # --- Конец добавления ---
    from services_veretevo.task_service import add_or_update_task
    add_or_update_task(task)
    logging.info(f"[DEBUG] add_or_update_task вызван для задачи: {task}")
    dep_chat_id = None
    dep_name = "Неизвестно"
    if dep_key and dep_key in DEPARTMENTS:
        dep_chat_id = DEPARTMENTS[dep_key].get('chat_id')
        dep_name = DEPARTMENTS[dep_key].get('name', 'Неизвестно')
    if dep_chat_id:
        from utils_veretevo.keyboards import get_task_action_keyboard
        group_keyboard = get_task_action_keyboard(task, None)
        sent_msg = await send_task_with_media(context, dep_chat_id, task, reply_markup=group_keyboard)
        if sent_msg:
            if "group_messages" not in task:
                task["group_messages"] = []
            task["group_messages"].append({
                "chat_id": dep_chat_id,
                "message_id": sent_msg.message_id
            })
            task["department_message_id"] = sent_msg.message_id
            add_or_update_task(task)
    chat_type = update.effective_chat.type if update.effective_chat else "private"
    user_id = update.effective_user.id if update.effective_user else None
    reply_markup = main_menu_keyboard(chat_type, user_id)
    await query.message.reply_text(
        f"Задача будет назначена в отдел: {dep_name}",
        reply_markup=reply_markup
    )
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logging.debug(f"Ошибка очистки клавиатуры: {e}")
    try:
        await query.message.delete()
    except Exception as e:
        logging.debug(f"Ошибка удаления сообщения с выбором сотрудника: {e}")
    context.user_data.pop('creating_task', None)
    context.user_data.pop('task_text', None)
    context.user_data.pop('media', None)
    context.user_data.pop('department', None)
    context.user_data.pop('department_member', None)
    return ConversationHandler.END

async def assign_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает назначение задачи ассистенту или без назначения.
    Сохраняет задачу, отправляет её в чат ассистентов, очищает временные данные пользователя.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    data = query.data
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logging.debug(f"assign_assistant: user_id={user_id}, data='{data}'")
    if data == "cancel_task":
        return await cancel_task_callback(update, context)
    await query.answer()
    author_name = update.effective_user.full_name if update.effective_user else "Неизвестно"
    assistant_id = None
    assistant_name = None
    # Получаем актуальные отделы напрямую из модуля
    from services_veretevo.department_service import DEPARTMENTS
    assistants = DEPARTMENTS.get('assistants', {}).get('members', {})
    if data.startswith("assign_"):
        if data == "assign_none":
            assistant_id = None
            assistant_name = "Без назначения"
        else:
            assistant_id = int(data.split("_")[1])
            assistant_name = assistants.get(str(assistant_id), "Неизвестно")
    if context.user_data is None:
        context.user_data = {}
    chat_id = update.effective_chat.id if update.effective_chat else 0
    task = {
        "id": int(datetime.datetime.now().timestamp() * 1000),
        "text": context.user_data.get('task_text', ""),
        "media": context.user_data.get('media') if context.user_data.get('media') else None,
        "status": "новая",
        "author_id": user_id,
        "author_name": author_name,
        "assistant_id": assistant_id,
        "assistant_name": assistant_name,
        "department": "assistants",
        "created_at": datetime.datetime.now().isoformat(),
        "chat_id": chat_id,
        "history": []
    }
    from services_veretevo.task_service import add_or_update_task
    add_or_update_task(task)
    logging.info(f"[DEBUG] add_or_update_task вызван для задачи: {task}")
    logging.info(f"[DEBUG] tasks после добавления: {tasks}")
    logging.info(f"[DEBUG] tasks после сохранения: {tasks}")
    from config_veretevo.env import ASSISTANTS_CHAT_ID
    from utils_veretevo.keyboards import get_task_action_keyboard
    assistant_keyboard = get_task_action_keyboard(task, None)
    sent_msg = await send_task_with_media(context, ASSISTANTS_CHAT_ID, task, reply_markup=assistant_keyboard)
    if sent_msg:
        if "group_messages" not in task:
            task["group_messages"] = []
        task["group_messages"].append({
            "chat_id": ASSISTANTS_CHAT_ID,
            "message_id": sent_msg.message_id
        })
        task["assistant_message_id"] = sent_msg.message_id
        add_or_update_task(task)
        logging.info(f"[DEBUG] add_or_update_task повторно вызван для задачи: {task}")
    if update.effective_chat and update.effective_chat.type == "private":
        reply_markup = main_menu_keyboard("private", user_id)
        await query.message.reply_text("Задача создана и направлена в чат ассистентов.", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Задача создана и направлена в чат ассистентов.")
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logging.debug(f"Ошибка очистки клавиатуры: {e}")
    try:
        await query.message.delete()
    except Exception as e:
        logging.debug(f"Ошибка удаления сообщения с выбором сотрудника: {e}")
    if context.user_data:
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_text', None)
        context.user_data.pop('media', None)
    return ConversationHandler.END

async def task_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    user_id = update.effective_user.id if update.effective_user else 0
    data = query.data
    chat_type = update.effective_chat.type if update.effective_chat else "unknown"
    logging.info(f"🎯 task_action_callback ВЫЗВАН: user_id={user_id}, chat_type={chat_type}, data='{data}'")
    
    # Загружаем актуальные задачи
    from services_veretevo.task_service import load_tasks, tasks
    load_tasks()
    logging.info(f"🎯 Загружено задач в память: {len(tasks)}")
    for task in tasks:
        logging.info(f"🎯 Задача в памяти: ID={task.get('id')}, текст='{task.get('text', 'N/A')}'")
    
    from services_veretevo.department_service import get_user_departments, DEPARTMENTS
    if data.startswith("take_"):
        logging.info(f"🎯 Обработка 'take' для data='{data}'")
        task_id = data.split("_", 1)[1]
        logging.info(f"🎯 task_id извлечен: '{task_id}'")
        try:
            task_id = int(task_id)
        except ValueError:
            logging.error(f"🎯 Неверный формат task_id: '{task_id}'")
            return
        task = get_task_by_id(task_id)
        if not task:
            logging.warning(f"🎯 Задача не найдена для ID: '{task_id}'")
            return
        logging.info(f"🎯 Задача найдена: {task.get('text', 'N/A')}")
        if task.get("status") != "новая":
            logging.info(f"🎯 Задача уже не новая, статус: {task.get('status')}")
            await query.answer("Задача уже не новая.", show_alert=True)
            return
        # Контроль доступа: только директор, ответственный или член отдела
        def has_task_access(task, user_id):
            if user_id == GENERAL_DIRECTOR_ID:
                return True
            if task.get("assistant_id") == user_id:
                return True
            dep_key = task.get("department")
            user_id_str = str(user_id)
            if dep_key and user_id_str in DEPARTMENTS.get(dep_key, {}).get("members", {}):
                return True
            return False
        if not has_task_access(task, user_id):
            await query.answer("Нет доступа к задаче.", show_alert=True)
            return
        task["assistant_id"] = user_id
        # Имя исполнителя ищем по отделу задачи
        dep_key = task.get("department")
        dep = DEPARTMENTS.get(dep_key, {})
        assistants = dep.get('members', {})
        task["assistant_name"] = assistants.get(str(user_id), "Неизвестно")
        task["status"] = "в работе"
        task.setdefault("history", []).append({"action": "take", "by": user_id})
        add_or_update_task(task)
        await update_task_messages(context, task_id, "в работе")
        # Уведомление как отдельный комментарий больше не отправляем для ассистентов
        return
    if data.startswith("finish_") or data.startswith("cancel_"):
        action, task_id = data.split("_", 1)
        logging.info(f"🎯 Обработка '{action}' для task_id='{task_id}'")
        try:
            task_id = int(task_id)
        except ValueError:
            logging.error(f"🎯 Неверный формат task_id: '{task_id}'")
            return
        task = get_task_by_id(task_id)
        if not task:
            logging.warning(f"🎯 Задача не найдена для ID: '{task_id}'")
            return
        logging.info(f"🎯 Задача найдена: {task.get('text', 'N/A')}")
        status = task.get("status")
        
        # Дополнительная проверка: запретить действия с завершенными/отмененными задачами
        if status in ['завершено', 'отменено']:
            await query.answer(f"Задача уже {status}.", show_alert=True)
            return
            
        is_director = user_id == GENERAL_DIRECTOR_ID
        user_id_str = str(user_id)
        is_assistant = user_id_str in DEPARTMENTS.get('assistants', {}).get('members', {})
        is_assistant_task = task.get("assistant_id") == user_id
        is_author = task.get("author_id") == user_id
        is_director_author = task.get("author_id") == GENERAL_DIRECTOR_ID
        
        # Подробное логирование для отладки
        logging.info(f"🎯 DEBUG: user_id={user_id}, is_director={is_director}, is_assistant={is_assistant}, is_assistant_task={is_assistant_task}, is_author={is_author}")
        logging.info(f"🎯 DEBUG: task.assistant_id={task.get('assistant_id')}, task.author_id={task.get('author_id')}")
        logging.info(f"🎯 DEBUG: DEPARTMENTS['assistants']['members']={DEPARTMENTS.get('assistants', {}).get('members', {})}")
        
        # Запретить повторные действия
        if action == "finish":
            if status == "завершено":
                await query.answer("Задача уже завершена.", show_alert=True)
                return
            # Кнопка "Завершить" работает для всех пользователей
            logging.info(f"🎯 Пользователь {user_id} завершает задачу {task_id}")
            task["status"] = "завершено"
            task.setdefault("history", []).append({"action": "finish", "by": user_id})
            add_or_update_task(task)
            # --- Синхронизация завершения с Todoist ---
            if task.get("todoist_task_id"):
                try:
                    close_task(task["todoist_task_id"])
                except Exception as e:
                    logging.error(f"[TODOIST] Ошибка при завершении задачи в Todoist: {e}")
            # --- Конец синхронизации ---
            await update_task_messages(context, task_id, "завершено")
            # Уведомление как отдельный комментарий больше не отправляем для ассистентов
            return
        if action == "cancel":
            if status == "отменено":
                await query.answer("Задача уже отменена.", show_alert=True)
                return
            # Кнопка "Отменить" только для автора или директора
            if not (is_director or is_author):
                logging.warning(f"🎯 Пользователь {user_id} не может отменить задачу {task_id}: не директор и не автор")
                await query.answer("Только автор или директор может отменить задачу.", show_alert=True)
                return
            logging.info(f"🎯 Пользователь {user_id} отменяет задачу {task_id}")
            task["status"] = "отменено"
            task.setdefault("history", []).append({"action": "cancel", "by": user_id})
            add_or_update_task(task)
            # --- Синхронизация отмены с Todoist ---
            if task.get("todoist_task_id"):
                try:
                    delete_task(task["todoist_task_id"])
                except Exception as e:
                    logging.error(f"[TODOIST] Ошибка при удалении задачи в Todoist: {e}")
            # --- Конец синхронизации ---
            await update_task_messages(context, task_id, "отменено")
            # Уведомление как отдельный комментарий больше не отправляем для ассистентов
            return

async def cancel_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает отмену создания задачи через callback-кнопку.
    Очищает временные данные пользователя и возвращает главное меню.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    query = update.callback_query
    await query.answer()
    
    # Удаляем сообщение с кнопками
    try:
        await query.message.delete()
    except Exception as e:
        logging.debug(f"Ошибка удаления сообщения при отмене: {e}")
    
    if context.user_data:
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_text', None)
        context.user_data.pop('media', None)
    
    chat_type = update.effective_chat.type if update.effective_chat else "private"
    user_id = update.effective_user.id if update.effective_user else None
    if chat_type == "private":
        reply_markup = main_menu_keyboard(chat_type, user_id)
        await query.message.reply_text("Создание задачи отменено.", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Создание задачи отменено.")
    return ConversationHandler.END

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает пользователю список задач его отделов.
    Если отделов несколько — предлагает выбрать отдел.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    logging.debug("list_tasks вызван")
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.message.reply_text("Ошибка: не удалось определить пользователя.")
        return
    department_service.load_departments()
    user_deps = department_service.get_user_departments(user_id)
    if not user_deps:
        await update.message.reply_text(
            "Вы не состоите ни в одном отделе.",
            reply_markup=main_menu_keyboard("private", user_id)
        )
        return
    if len(user_deps) == 1:
        dep_key, dep_name = user_deps[0]
        await show_department_tasks(update, context, dep_key, dep_name)
        return
    keyboard = [[InlineKeyboardButton(dep_name, callback_data=f"choose_dep_{dep_key}")] for dep_key, dep_name in user_deps]
    # Добавляю кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")])
    await update.message.reply_text(
        "Выберите отдел:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def tasks_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор отдела для просмотра задач через callback-кнопку.
    Показывает задачи выбранного отдела.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    # Получаем актуальные отделы напрямую из модуля
    from services_veretevo.department_service import DEPARTMENTS
    
    logging.debug(f"tasks_type_callback вызван, data={getattr(update.callback_query, 'data', None)}")
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            logging.debug(f"Ошибка query.answer(): {e}")
    user_id = update.effective_user.id if update.effective_user else 0
    data = query.data
    from services_veretevo.task_service import load_tasks
    load_tasks()
    if data == "cancel_task":
        # Удаляем сообщение с кнопками
        try:
            await query.message.delete()
        except Exception as e:
            logging.debug(f"Ошибка удаления сообщения при отмене: {e}")
        
        chat_type = update.effective_chat.type if update.effective_chat else "private"
        reply_markup = main_menu_keyboard(chat_type, user_id)
        await query.message.reply_text("Просмотр задач отменён.", reply_markup=reply_markup)
        return
    if data.startswith("choose_dep_"):
        dep_key = data[len("choose_dep_"):]
        if dep_key not in DEPARTMENTS:
            await query.message.reply_text("Ошибка: отдел не найден.")
            return
        await show_department_tasks(update, context, dep_key, DEPARTMENTS[dep_key]["name"])
        return
    # Можно добавить обработку других типов задач (личные, ассистентов и т.д.)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает голосовые сообщения в любом контексте.
    Если пользователь в процессе создания задачи - транскрибирует и предлагает создать задачу.
    Иначе показывает только транскрипцию.
    """
    # Получаем актуальные отделы напрямую из модуля
    from services_veretevo.department_service import DEPARTMENTS
    
    logging.info(f"[DEBUG] handle_voice_message вызван")
    if not update.message.voice:
        logging.info(f"[DEBUG] Нет голосового сообщения")
        return
    
    file_id = update.message.voice.file_id
    logging.info(f"[DEBUG] Получено голосовое сообщение: file_id={file_id}")
    
    # Скачиваем файл
    file = await context.bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
        await file.download_to_drive(temp_audio.name)
        logging.info(f"[DEBUG] Аудиофайл сохранен: {temp_audio.name}")
        
        if voice_transcriber:
            try:
                transcript = voice_transcriber.process_audio_file(temp_audio.name)
            except Exception as e:
                logging.error(f"[ОШИБКА] Ошибка при транскрипции: {e}")
                transcript = None
        else:
            transcript = None
            logging.error(f"[DEBUG] voice_transcriber равен None!")
            await update.message.reply_text("⚠️ Служба распознавания речи недоступна.")
    
    os.unlink(temp_audio.name)
    logging.info(f"[DEBUG] Временный файл удален")
    
    if transcript and transcript.strip():
        # Проверяем, есть ли отдел в тексте
        improved = improve_task_text(transcript)
        dep_key = extract_department_from_text(improved)
        
        logging.info(f"[DEBUG] Транскрипция: '{transcript}'")
        logging.info(f"[DEBUG] Улучшенный текст: '{improved}'")
        logging.info(f"[DEBUG] Найденный отдел: '{dep_key}'")
        
        if dep_key and dep_key in DEPARTMENTS:
            # Если отдел определен - предлагаем создать задачу
            dep_name = DEPARTMENTS[dep_key]['name']
            keyboard = [[InlineKeyboardButton("📌 Создать задачу", callback_data=f"create_task_from_voice_{dep_key}")]]
            logging.info(f"[DEBUG] Создаем кнопку для отдела: {dep_name}")
            await update.message.reply_text(
                f"🎤 Распознанный текст:\n\n{improved}\n\nОбнаружен отдел: {dep_name}\nХотите создать задачу?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            logging.info(f"[DEBUG] Отдел не найден, показываем только транскрипцию")
            await update.message.reply_text(f"🎤 Распознанный текст:\n\n{transcript}")
    else:
        await update.message.reply_text("⚠️ Не удалось распознать речь. Попробуйте еще раз.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые команды пользователя из главного меню (создание задачи, список задач).
    Работает только в личных чатах и только с командами меню.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    logging.debug(f"handle_text вызван, текст: {update.message.text}")
    text = update.message.text
    
    # Проверяем, что это команды меню
    if text in ["📌 Новая задача", "📋 Список задач", "Мои задачи"]:
        # Обрабатываем команды только в личных чатах
        if text == "📌 Новая задача":
            return await new_task_start(update, context)
        elif text == "📋 Список задач":
            return await list_tasks(update, context)
        elif text == "Мои задачи":
            return await view_personal_tasks(update, context)
    
    # Если это не команда меню, не обрабатываем
    logging.debug(f"handle_text: пропускаем сообщение '{text}' - не является командой меню")

async def show_department_tasks(update, context, dep_key, dep_name):
    """
    Показывает список задач выбранного отдела пользователю.
    Проверяет права доступа, отправляет задачи с клавиатурой действий.

    Args:
        update: Объект обновления Telegram (Update или CallbackQuery).
        context: Контекст выполнения.
        dep_key (str): Ключ отдела.
        dep_name (str): Название отдела.
    """
    # Получаем актуальные отделы напрямую из модуля
    from services_veretevo.department_service import DEPARTMENTS
    
    import logging
    user_id = update.effective_user.id if update.effective_user else None
    dep = DEPARTMENTS.get(dep_key)
    members = dep.get("members", {}) if dep else {}
    chat_type = update.effective_chat.type if update.effective_chat else "unknown"
    logging.info(f"[DEBUG] show_department_tasks: user_id={user_id}, dep_key={dep_key}, members={list(members.keys())}, chat_type={chat_type}")
    def reply(text, **kwargs):
        if hasattr(update, 'message') and update.message:
            return update.message.reply_text(text, **kwargs)
        elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message:
            return update.callback_query.message.reply_text(text, **kwargs)
    if not dep or str(user_id) not in members:
        await reply("У вас нет доступа к этому отделу.")
        return
    from services_veretevo.task_service import get_tasks
    tasks = get_tasks()
    # Подробное логирование задач по отделу
    for t in tasks:
        if t.get("department") == dep_key:
            logging.info(f"[DEBUG] dep_key={dep_key}, задача: {t.get('text')}, status={t.get('status')}")
    dep_tasks = [t for t in tasks if t.get("department") == dep_key and t.get("status") in ("новая", "в работе")]
    logging.info(f"[DEBUG] show_department_tasks: dep_key={dep_key}, найдено задач={len(dep_tasks)} (статусы: {[t.get('status') for t in dep_tasks]}), chat_type={chat_type}")
    if not dep_tasks:
        await reply(f"В отделе {dep_name} нет задач.")
        return
    await reply(f"📋 Задачи отдела {dep_name}:")
    for task in dep_tasks:
        # В группах показываем кнопки всем участникам отдела, но при нажатии проверяем права
        # В личных чатах показываем кнопки только тем, кто имеет права
        department_members = list(members.keys())
        
        if chat_type == "private":
            # В личном чате - показываем кнопки только тем, кто имеет права
            keyboard = get_task_action_keyboard(task, user_id, department_members=department_members)
        else:
            # В группе - показываем кнопки всем участникам отдела
            keyboard = get_task_action_keyboard(task, None, department_members=department_members)
        
        # Логируем состав кнопок
        button_texts = []
        if keyboard and hasattr(keyboard, 'inline_keyboard'):
            try:
                for row in keyboard.inline_keyboard:
                    for btn in row:
                        button_texts.append(str(getattr(btn, 'text', btn)))
                logging.info(f"[DEBUG] Кнопки для задачи id={task.get('id')}, chat_type={chat_type}, user_id={user_id}: {button_texts}")
            except Exception as e:
                logging.error(f"[DEBUG] Ошибка логирования кнопок: {e}")
        else:
            logging.info(f"[DEBUG] Кнопки для задачи id={task.get('id')} не показываем (статус: {task.get('status')})")
        
        try:
            logging.info(f"[DEBUG] Отправка задачи id={task.get('id')} в чат {update.effective_chat.id} с кнопками: {button_texts}")
            sent_msg = await send_task_with_media(context, update.effective_chat.id, task, reply_markup=keyboard)
            # Сохраняем message_id и chat_id для личного чата
            if update.effective_chat and update.effective_chat.type == "private" and sent_msg:
                if 'private_messages' not in task:
                    task['private_messages'] = []
                task['private_messages'].append({
                    'chat_id': update.effective_chat.id,
                    'message_id': sent_msg.message_id
                })
                add_or_update_task(task)
        except Exception as e:
            logging.debug(f"Ошибка отправки задачи {task.get('id')}: {e}")
    # Удаляю финальные сообщения с предложением вернуться в главное меню
    # Было:
    # if update.effective_chat and update.effective_chat.type == "private":
    #     reply_markup = main_menu_keyboard("private", user_id)
    #     await update.effective_message.reply_text("Вы можете вернуться в главное меню.", reply_markup=reply_markup)
    # else:
    #     await reply("Вы можете вернуться в главное меню.")

async def view_personal_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"[DEBUG] update: {update}")
    logging.info(f"[DEBUG] effective_chat: {getattr(update, 'effective_chat', None)}")
    logging.info(f"[DEBUG] effective_chat.type: {getattr(getattr(update, 'effective_chat', None), 'type', None)}")
    logging.info(f"[DEBUG] message: {getattr(update, 'message', None)}")
    logging.info(f"[DEBUG] callback_query: {getattr(update, 'callback_query', None)}")
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("Ошибка: не удалось определить пользователя.")
        else:
            await update.effective_chat.send_message("Ошибка: не удалось определить пользователя.")
        return
    from services_veretevo.task_service import get_tasks
    from services_veretevo import department_service
    tasks = get_tasks()
    my_tasks = [t for t in tasks if str(t.get("assistant_id")) == str(user_id) and t.get("status") in ("новая", "в работе")]
    if not my_tasks:
        msg = "❗ У вас нет задач."
        if update.effective_chat and update.effective_chat.type == "private":
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(msg)
            else:
                await update.effective_chat.send_message(msg)
        return
    # Для формирования кнопок нужен список участников отдела
    for task in my_tasks:
        dep_key = task.get("department")
        dep = DEPARTMENTS.get(dep_key, {})
        members = dep.get("members", {})
        department_members = list(members.keys())
        keyboard = get_task_action_keyboard(task, user_id, department_members=department_members)
        try:
            sent_msg = await send_task_with_media(context, update.effective_chat.id, task, reply_markup=keyboard)
            # Сохраняем message_id и chat_id для личного чата
            if update.effective_chat and update.effective_chat.type == "private" and sent_msg:
                if 'private_messages' not in task:
                    task['private_messages'] = []
                task['private_messages'].append({
                    'chat_id': update.effective_chat.id,
                    'message_id': sent_msg.message_id
                })
                add_or_update_task(task)
        except Exception as e:
            logging.debug(f"Ошибка отправки задачи {task.get('id')}: {e}")

async def update_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительного обновления сообщений задачи"""
    user_id = update.effective_user.id
    
    if user_id != GENERAL_DIRECTOR_ID:
        await update.message.reply_text("Эта команда доступна только генеральному директору!")
        return
    
    # Получаем ID задачи из команды (например: /update_messages 1753478314540)
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /update_messages <ID_задачи>")
        return
    
    try:
        task_id = int(args[0])
        force_update_task_messages(task_id, context.application)
        await update.message.reply_text(f"Обновление сообщений для задачи {task_id} запущено!")
    except ValueError:
        await update.message.reply_text("Неверный ID задачи. Используйте число.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Регистрация обработчика для кнопки 'Мои задачи'
def register_task_handlers(application: Application) -> None:
    """
    Регистрирует все обработчики задач в приложении Telegram.

    Args:
        application (Application): Экземпляр Telegram Application.
    """
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^\U0001F4CC Новая задача$"), new_task_start)],
        states={
            WAITING_FOR_TASK_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_task_text),
                MessageHandler(filters.PHOTO, receive_task_text),
                MessageHandler(filters.Document.ALL, receive_task_text),
                MessageHandler(filters.VIDEO, receive_task_text),
                MessageHandler(filters.AUDIO, receive_task_text),
                MessageHandler(filters.VOICE, receive_task_text),
            ],
            WAITING_FOR_DEPARTMENT_MEMBER: [CallbackQueryHandler(choose_department_create_callback, pattern=r"^choose_dep_create_.*$")],
            WAITING_FOR_ASSIGN_TYPE: [CallbackQueryHandler(assign_type_callback, pattern=r"^(assign_.*|assign_none|cancel_task)$")],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), cancel_task_callback)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(task_action_callback, pattern=r"^(take_|finish_|cancel_).*$"))
    application.add_handler(MessageHandler(filters.Regex("^📋 Список задач$"), list_tasks))
    application.add_handler(MessageHandler(filters.Regex("^Мои задачи$"), view_personal_tasks))
    application.add_handler(CallbackQueryHandler(tasks_type_callback, pattern=r"^(choose_dep_.*|cancel_task)$"))
    # Обработчик отмены при создании задачи
    application.add_handler(CallbackQueryHandler(cancel_task_callback, pattern=r"^cancel_create_task$"))
    # Обработчик создания задачи из голосового сообщения
    application.add_handler(CallbackQueryHandler(create_task_from_voice_callback, pattern=r"^create_task_from_voice_.*$"))
    # Команда для обновления сообщений (только для директора)
    from telegram.ext import CommandHandler
    application.add_handler(CommandHandler("update_messages", update_messages_command))
    # Обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    # Обработчик текстовых команд меню (только для личных чатов)
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_text))

def extract_department_from_text(text: str) -> str:
    """
    Пытается найти отдел по ключу 'отдел' и сокращениям в тексте.
    Возвращает ключ отдела или None.
    """
    text = text.lower()
    # Словарь сокращений и альтернативных названий
    dep_map = {
        'assistants': ['ассистенты', 'ассистент', 'ассист', 'помощник', 'помощники', 'помощь', 'помогите'],
        'carpenters': ['плотники', 'плотник', 'плотницкие', 'плотницкая'],
        'maintenance': ['эксплуатация', 'эксплуат', 'техэксплуатация', 'техобслуживание', 'обслуживание'],
        'tech': ['тех команда', 'техкоманда', 'тех', 'технический', 'техники', 'техник'],
        'maids': ['горничные', 'горничная', 'уборка', 'уборщицы', 'уборщица', 'клининг'],
        'reception': ['ресепшен', 'ресеп', 'приём', 'прием', 'администрация', 'админ'],
        'security': ['охрана', 'охранник', 'безопасность', 'секьюрити', 'сторож'],
        'finance': ['финансы', 'финанс', 'бухгалтерия', 'бухгалтер', 'касса', 'деньги', 'оплата'],
    }
    
    # Ищем фразу "отдел ..." или "в отдел ..."
    match = re.search(r'(?:отдел|в отдел)\s+([\w\-]+)', text)
    if match:
        word = match.group(1)
        for dep_key, variants in dep_map.items():
            if word in variants or word in dep_key or word in DEPARTMENTS.get(dep_key, {}).get('name', '').lower():
                return dep_key
    
    # Ищем просто упоминание отдела по сокращениям
    for dep_key, variants in dep_map.items():
        for v in variants:
            if v in text:
                return dep_key
    
    # Ищем по ключевым словам в контексте
    context_keywords = {
        'assistants': ['помощь', 'помогите', 'вопрос', 'консультация'],
        'carpenters': ['дерево', 'мебель', 'ремонт', 'постройка'],
        'maintenance': ['ремонт', 'обслуживание', 'техника', 'оборудование'],
        'tech': ['компьютер', 'интернет', 'сеть', 'программа'],
        'maids': ['уборка', 'чистота', 'постель', 'белье'],
        'reception': ['регистрация', 'гость', 'номер', 'бронирование'],
        'security': ['безопасность', 'пропуск', 'контроль', 'досмотр'],
        'finance': ['оплата', 'счет', 'деньги', 'бухгалтерия'],
    }
    
    for dep_key, keywords in context_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return dep_key
    
    return None
