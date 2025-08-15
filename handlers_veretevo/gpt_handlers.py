import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CallbackContext, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from services_veretevo.gpt_service import gpt_service
from services_veretevo.department_service import DEPARTMENTS
import json

# Глобальные переменные для хранения состояния
gpt_contexts = {}  # {chat_id: {"question": "...", "answer": "...", "department": "..."}}

async def handle_message_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения в группах и предлагает GPT-подсказки"""
    
    logging.info(f"[GPT DEBUG] === НАЧАЛО ОБРАБОТКИ GPT ===")
    logging.info(f"[GPT DEBUG] Получено сообщение в чате {update.message.chat.id} от пользователя {update.message.from_user.id}")
    logging.info(f"[GPT DEBUG] Тип чата: {update.message.chat.type}")
    logging.info(f"[GPT DEBUG] Название чата: {update.message.chat.title}")
    logging.info(f"[GPT DEBUG] Текст сообщения: '{update.message.text}'")
    logging.info(f"[GPT DEBUG] Пользователь: {update.message.from_user.first_name} {update.message.from_user.last_name}")
    logging.info(f"[GPT DEBUG] Username: {update.message.from_user.username}")
    
    # Проверяем, что это группа
    if update.message.chat.type not in ['group', 'supergroup']:
        logging.info(f"[GPT DEBUG] Пропускаем - не группа")
        return
    
    # Проверяем, что это группа
    if update.message.chat.type not in ['group', 'supergroup']:
        logging.info(f"[GPT DEBUG] Пропускаем - не группа: {update.message.chat.type}")
        return
    
    # Проверяем, что это не сообщение от бота
    if update.message.from_user.is_bot:
        logging.info(f"[GPT DEBUG] Пропускаем - сообщение от бота")
        return
    
    # Проверяем, что это НЕ директор (подсказки появляются для сообщений других людей)
    if update.message.from_user.id == GENERAL_DIRECTOR_ID:
        logging.info(f"[GPT DEBUG] Пропускаем - сообщение от директора")
        return
    
    message_text = update.message.text
    if not message_text or len(message_text.strip()) < 3:
        logging.info(f"[GPT DEBUG] Пропускаем - короткое сообщение или пустое")
        return
    
    logging.info(f"[GPT DEBUG] Обрабатываем сообщение: '{message_text}'")
    
    # Получаем информацию об отделе
    department = get_department_from_chat(update.message.chat.id)
    
    # Проверяем, что это НЕ чат Ассистентов (отключаем GPT подсказки для этого чата)
    if update.message.chat.id == -1002766433811:  # Ассистенты
        logging.info(f"[GPT DEBUG] Пропускаем - GPT подсказки отключены для чата Ассистентов")
        return
    
    # Отправляем GPT-подсказку директору в личный чат (приватно)
    try:
        logging.info(f"[GPT DEBUG] Создаем GPT-подсказку для директора")
        # Создаем клавиатуру с GPT-подсказкой
        # Используем только ID сообщения и чата, текст будем получать отдельно
        callback_data = f"gpt_gen:{update.message.message_id}:{update.message.chat.id}"
        logging.info(f"[GPT DEBUG] Создаем кнопку с callback_data: {callback_data}")
        logging.info(f"[GPT DEBUG] Message ID: {update.message.message_id}, Chat ID: {update.message.chat.id}")
        keyboard = [
            [InlineKeyboardButton("💡 GPT-ответ", callback_data=callback_data)]
        ]
        
        # Добавляем варианты ответа если есть
        variants = gpt_service.get_answer_variants(message_text)
        if variants:
            variant_buttons = []
            for variant in variants:
                variant_buttons.append(InlineKeyboardButton(
                    variant["text"], 
                    callback_data=f"gpt_variant:{update.message.message_id}:{update.message.chat.id}:{variant['callback_data']}"
                ))
            keyboard.append(variant_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем подсказку директору в личный чат
        await context.bot.send_message(
            chat_id=GENERAL_DIRECTOR_ID,
            text=f"🤖 GPT-подсказка из чата {update.message.chat.title}:\n\n💬 Сообщение: {message_text}\n\nЧто ответить?",
            reply_markup=reply_markup
        )
        
        logging.info(f"[GPT DEBUG] Подсказка отправлена директору в личный чат")
        
    except Exception as e:
        logging.error(f"Ошибка отправки GPT-подсказки: {e}")

async def handle_gpt_generate(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки GPT-ответ"""
    
    logging.info(f"[GPT DEBUG] === НАЧАЛО ОБРАБОТКИ GPT_GENERATE ===")
    logging.info(f"[GPT DEBUG] Получен callback: {update.callback_query.data}")
    logging.info(f"[GPT DEBUG] Пользователь: {update.callback_query.from_user.id}")
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer("🤖 Генерирую ответ...")
    
    # Получаем ID сообщения и ID чата
    data_parts = update.callback_query.data.split(":")
    message_id = int(data_parts[1])
    chat_id = int(data_parts[2])
    
    # Используем заглушку для текста (в реальной реализации нужно сохранять в базе)
    original_text = "Сообщение из группового чата"
    
    # Получаем информацию о чате
    try:
        chat = await context.bot.get_chat(chat_id)
        logging.info(f"[GPT DEBUG] Получен чат: {chat.title}")
    except Exception as e:
        logging.error(f"[GPT DEBUG] Ошибка получения чата: {e}")
        await update.callback_query.edit_message_text("❌ Не удалось получить информацию о чате")
        return
    
    # Получаем отдел
    department = get_department_from_chat(chat_id)
    
    # Генерируем 3 варианта ответа через GPT
    responses = []
    logging.info(f"[GPT DEBUG] Начинаем генерацию для чата {chat_id}, отдел: {department}")
    for i in range(3):
        try:
            logging.info(f"[GPT DEBUG] Генерируем вариант {i+1}")
            response_data = await gpt_service.get_smart_response(original_text, department)
            responses.append(response_data['answer'])
            logging.info(f"[GPT DEBUG] Вариант {i+1} успешно сгенерирован")
        except Exception as e:
            logging.error(f"[GPT DEBUG] Ошибка генерации варианта {i+1}: {e}")
            responses.append(f"Вариант {i+1}: Ошибка генерации")
    
    # Создаем клавиатуру с цифрами
    keyboard = [
        [InlineKeyboardButton("1", callback_data=f"gpt_choose:{chat_id}:1")],
        [InlineKeyboardButton("2", callback_data=f"gpt_choose:{chat_id}:2")],
        [InlineKeyboardButton("3", callback_data=f"gpt_choose:{chat_id}:3")],
        [InlineKeyboardButton("🔄 Другие варианты", callback_data=f"gpt_regenerate:{message_id}:{chat_id}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст с вариантами
    variants_text = f"🤖 Варианты ответа на: '{original_text}'\n\n"
    for i, response in enumerate(responses, 1):
        variants_text += f"{i}. {response}\n\n"
    variants_text += "Выберите вариант:"
    
    # Обновляем сообщение с вариантами ответов
    await update.callback_query.edit_message_text(
        text=variants_text,
        reply_markup=reply_markup
    )
    
    logging.info(f"[GPT DEBUG] Показаны варианты ответов для чата {chat_id}")

async def handle_gpt_variant(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки с вариантом ответа"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer()
    
    # Получаем данные
    parts = update.callback_query.data.split(":")
    message_id = int(parts[1])
    chat_id = int(parts[2])
    variant = parts[3]
    
    # Получаем информацию о чате
    try:
        chat = await context.bot.get_chat(chat_id)
        logging.info(f"[GPT DEBUG] Получен чат: {chat.title}")
    except Exception as e:
        logging.error(f"[GPT DEBUG] Ошибка получения чата: {e}")
        await update.callback_query.edit_message_text("❌ Не удалось получить информацию о чате")
        return
    
    # Формируем ответ в зависимости от варианта
    if variant == "gpt_yes":
        answer = "✅ Да, можно. Приступайте к работе."
    elif variant == "gpt_no":
        answer = "❌ Нет, не стоит. Давайте обсудим альтернативные варианты."
    elif variant == "gpt_now":
        answer = "⏰ Сейчас займусь этим вопросом. Подождите немного."
    elif variant == "gpt_later":
        answer = "📅 Сейчас не могу, но обязательно решу позже. Напомните через час."
    elif variant == "gpt_think":
        answer = "🤔 Нужно подумать над этим вопросом. Дайте мне время на размышление."
    elif variant == "gpt_urgent_help":
        answer = "🆘 Понимаю, что срочно. Сейчас свяжусь с вами и решим проблему."
    elif variant == "gpt_contact":
        answer = "📞 Свяжусь с вами лично, чтобы обсудить детали."
    elif variant == "gpt_analyze":
        answer = "🤖 Проанализирую ситуацию и дам подробный ответ через несколько минут."
    else:
        answer = "🤔 Нужно подумать над этим вопросом."
    
    # Получаем отдел
    department = get_department_from_chat(chat_id)
    
    # Для демонстрации используем заглушку текста
    original_text = "Сообщение из группового чата"
    
    # Формируем ответ в зависимости от варианта
    if variant == "gpt_yes":
        answer = "✅ Да"
    elif variant == "gpt_no":
        answer = "❌ Нет"
    elif variant == "gpt_analyze":
        # Для GPT-анализа отправляем в личный чат для выбора вариантов
        await update.callback_query.answer("🤖 Анализирую вопрос...")
        
        # Генерируем варианты ответов через GPT
        response_data = await gpt_service.get_smart_response(original_text, department)
        
        # Создаем клавиатуру с вариантами
        keyboard = [
            [InlineKeyboardButton(
                f"🤖 {response_data['answer'][:30]}...", 
                callback_data=f"gpt_send:{chat_id}:{urllib.parse.quote(response_data['answer'])}"
            )],
            [InlineKeyboardButton(
                "🔄 Другой вариант", 
                callback_data=f"gpt_regenerate:{message_id}:{chat_id}"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем варианты в личный чат
        await context.bot.send_message(
            chat_id=GENERAL_DIRECTOR_ID,
            text=f"🤖 Варианты ответа на: '{original_text}'\n\nВыберите подходящий:",
            reply_markup=reply_markup
        )
        
        # Удаляем исходную подсказку
        await update.callback_query.edit_message_reply_markup(reply_markup=None)
        
        logging.info(f"[GPT DEBUG] Варианты GPT отправлены в личный чат")
        return
    else:
        answer = "🤔 Нужно подумать над этим вопросом."
    
    # Сохраняем контекст
    gpt_contexts[chat_id] = {
        "question": original_text,
        "answer": answer,
        "department": department,
        "type": "variant"
    }
    
    # Отправляем ответ в групповой чат
    answer_text = f"📣 Ответ от директора:\n\n{answer}"
    
    keyboard = [
        [InlineKeyboardButton("💾 Сохранить как шаблон", callback_data="gpt_save_template")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=answer_text,
        reply_markup=reply_markup
    )
    
    # Удаляем подсказку (убираем кнопки)
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    
    logging.info(f"[GPT DEBUG] Вариант ответа отправлен в чат {chat_id}")

async def handle_save_template(update: Update, context: CallbackContext):
    """Обрабатывает сохранение ответа как шаблона"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    chat_id = update.callback_query.message.chat.id
    
    if chat_id not in gpt_contexts:
        await update.callback_query.answer("❌ Контекст не найден", show_alert=True)
        return
    
    context_data = gpt_contexts[chat_id]
    
    # Сохраняем в базу знаний
    success = gpt_service.save_answer_template(
        context_data["question"],
        context_data["answer"],
        context_data["department"]
    )
    
    if success:
        await update.callback_query.answer("✅ Ответ сохранен в базу знаний!")
        
        # Обновляем сообщение
        current_text = update.callback_query.message.text
        new_text = current_text + "\n\n💾 Сохранено в базу знаний"
        
        await update.callback_query.edit_message_text(
            text=new_text,
            reply_markup=None
        )
        
        # Очищаем контекст
        del gpt_contexts[chat_id]
    else:
        await update.callback_query.answer("❌ Ошибка сохранения", show_alert=True)

async def handle_gpt_stats(update: Update, context: CallbackContext):
    """Показывает статистику базы знаний"""
    
    # Проверяем права доступа
    if update.message.from_user.id != GENERAL_DIRECTOR_ID:
        return
    
    stats = gpt_service.get_cache_stats()
    
    stats_text = f"""
📊 Статистика базы знаний GPT:

📝 Всего ответов: {stats['total_answers']}
💾 Размер файла: {stats['file_size']} байт
🕒 Последнее сохранение: {stats['last_save']}
    """
    
    await update.message.reply_text(stats_text)

def get_department_from_chat(chat_id: int) -> str:
    """Определяет отдел по ID чата"""
    # Определяем отдел по ID чата
    if chat_id == -1002766433811:  # Ассистенты
        return "assistants"
    elif chat_id == -1002874667453:  # Плотники
        return "carpenters"
    elif chat_id == -1002295933154:  # Охрана
        return "security"
    elif chat_id == -1002844492561:  # Финансы
        return "finance"
    elif chat_id == -1002634456712:  # Стройка
        return "construction"
    elif chat_id == -1002588088668:  # Руководители
        return "management"
    elif chat_id == -4883128031:  # Инфо
        return "info"
    else:
        return ""

def register_gpt_handlers(application):
    """Регистрирует обработчики GPT-подсказок"""
    
    # GPT обработчик
    application.add_handler(
        MessageHandler(
            (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP) & filters.TEXT & ~filters.COMMAND,
            handle_message_in_group
        )
    )
    
    # Обработчики callback-запросов
    application.add_handler(
        CallbackQueryHandler(handle_gpt_generate, pattern="^gpt_gen:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_gpt_variant, pattern="^gpt_variant:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_gpt_send, pattern="^gpt_send:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_gpt_quick, pattern="^gpt_quick:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_gpt_regenerate, pattern="^gpt_regenerate:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_gpt_choose, pattern="^gpt_choose:")
    )
    
    application.add_handler(
        CallbackQueryHandler(handle_save_template, pattern="^gpt_save_template$")
    )
    
    # Обработчик статистики
    application.add_handler(
        CommandHandler("gpt_stats", handle_gpt_stats)
    )
    
    logging.info("✅ Обработчики GPT-подсказок зарегистрированы")

async def handle_gpt_send(update: Update, context: CallbackContext):
    """Отправляет выбранный GPT ответ в чат"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer("📤 Отправляю ответ...")
    
    # Получаем данные
    data_parts = update.callback_query.data.split(":")
    chat_id = int(data_parts[1])
    
    # Используем заглушку для ответа (в реальной реализации нужно сохранять в базе)
    answer = "🤖 Ответ сгенерирован GPT"
    
    # Отправляем ответ в групповой чат
    answer_text = f"📣 Ответ от директора:\n\n{answer}"
    
    # Создаем клавиатуру с кнопкой сохранения
    keyboard = [
        [InlineKeyboardButton("💾 Сохранить как шаблон", callback_data="gpt_save_template")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=answer_text,
        reply_markup=reply_markup
    )
    
    # Удаляем варианты ответов
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    
    logging.info(f"[GPT DEBUG] Ответ отправлен в чат {chat_id}")

async def handle_gpt_quick(update: Update, context: CallbackContext):
    """Отправляет быстрый ответ в чат"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer("📤 Отправляю быстрый ответ...")
    
    # Получаем данные
    data_parts = update.callback_query.data.split(":")
    chat_id = int(data_parts[1])
    variant = data_parts[2]
    
    # Формируем ответ в зависимости от варианта
    if variant == "gpt_yes":
        answer = "✅ Да"
    elif variant == "gpt_no":
        answer = "❌ Нет"
    elif variant == "gpt_analyze":
        # Для GPT-анализа отправляем в личный чат для выбора вариантов
        await update.callback_query.answer("🤖 Анализирую вопрос...")
        
        # Получаем отдел
        department = get_department_from_chat(chat_id)
        
        # Генерируем варианты ответов через GPT
        response_data = await gpt_service.get_smart_response("Сообщение из группового чата", department)
        
        # Создаем клавиатуру с вариантами
        keyboard = [
            [InlineKeyboardButton(
                f"🤖 {response_data['answer'][:30]}...", 
                callback_data=f"gpt_send:{chat_id}:gpt_response"
            )],
            [InlineKeyboardButton(
                "🔄 Другой вариант", 
                callback_data=f"gpt_regenerate:0:{chat_id}"
            )]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем варианты в личный чат
        await context.bot.send_message(
            chat_id=GENERAL_DIRECTOR_ID,
            text=f"🤖 Варианты ответа на сложный вопрос:\n\nВыберите подходящий:",
            reply_markup=reply_markup
        )
        
        # Удаляем исходную подсказку
        await update.callback_query.edit_message_reply_markup(reply_markup=None)
        
        logging.info(f"[GPT DEBUG] Варианты GPT отправлены в личный чат")
        return
    else:
        answer = "🤔 Нужно подумать над этим вопросом."
    
    # Отправляем ответ в групповой чат
    answer_text = f"📣 Ответ от директора:\n\n{answer}"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=answer_text
    )
    
    # Удаляем варианты ответов
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    
    logging.info(f"[GPT DEBUG] Быстрый ответ отправлен в чат {chat_id}")

async def handle_gpt_regenerate(update: Update, context: CallbackContext):
    """Генерирует новый вариант ответа"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer("🔄 Генерирую новый вариант...")
    
    # Получаем данные
    data_parts = update.callback_query.data.split(":")
    message_id = int(data_parts[1])
    chat_id = int(data_parts[2])
    original_text = "Сообщение из группового чата"
    
    # Получаем отдел
    department = get_department_from_chat(chat_id)
    
    # Генерируем 3 новых варианта ответа
    responses = []
    logging.info(f"[GPT DEBUG] Начинаем генерацию для чата {chat_id}, отдел: {department}")
    for i in range(3):
        try:
            logging.info(f"[GPT DEBUG] Генерируем вариант {i+1}")
            response_data = await gpt_service.get_smart_response(original_text, department)
            responses.append(response_data['answer'])
            logging.info(f"[GPT DEBUG] Вариант {i+1} успешно сгенерирован")
        except Exception as e:
            logging.error(f"[GPT DEBUG] Ошибка генерации варианта {i+1}: {e}")
            responses.append(f"Вариант {i+1}: Ошибка генерации")
    
    # Создаем клавиатуру с цифрами
    keyboard = [
        [InlineKeyboardButton("1", callback_data=f"gpt_choose:{chat_id}:1")],
        [InlineKeyboardButton("2", callback_data=f"gpt_choose:{chat_id}:2")],
        [InlineKeyboardButton("3", callback_data=f"gpt_choose:{chat_id}:3")],
        [InlineKeyboardButton("🔄 Еще варианты", callback_data=f"gpt_regenerate:{message_id}:{chat_id}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст с вариантами
    variants_text = f"🤖 Новые варианты ответа на: '{original_text}'\n\n"
    for i, response in enumerate(responses, 1):
        variants_text += f"{i}. {response}\n\n"
    variants_text += "Выберите вариант:"
    
    await update.callback_query.edit_message_text(
        text=variants_text,
        reply_markup=reply_markup
    )
    
    logging.info(f"[GPT DEBUG] Сгенерирован новый вариант для чата {chat_id}")

async def handle_gpt_choose(update: Update, context: CallbackContext):
    """Обрабатывает выбор варианта ответа по цифре"""
    
    # Проверяем права доступа
    if update.callback_query.from_user.id != GENERAL_DIRECTOR_ID:
        await update.callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await update.callback_query.answer("📤 Отправляю выбранный ответ...")
    
    # Получаем данные
    data_parts = update.callback_query.data.split(":")
    chat_id = int(data_parts[1])
    choice = int(data_parts[2])
    
    # Используем заглушку для ответа (в реальной реализации нужно сохранять варианты)
    answer = f"🤖 Вариант {choice}: Ответ сгенерирован GPT"
    
    # Отправляем ответ в групповой чат
    answer_text = f"📣 Ответ от директора:\n\n{answer}"
    
    # Создаем клавиатуру с кнопкой сохранения
    keyboard = [
        [InlineKeyboardButton("💾 Сохранить как шаблон", callback_data="gpt_save_template")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=answer_text,
        reply_markup=reply_markup
    )
    
    # Удаляем варианты ответов
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    
    logging.info(f"[GPT DEBUG] Выбранный ответ отправлен в чат {chat_id}")