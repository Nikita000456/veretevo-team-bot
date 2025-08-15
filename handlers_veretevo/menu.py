import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from utils_veretevo.keyboards import main_menu_keyboard
from telegram.ext import ChatMemberHandler
from services_veretevo import department_service
from telegram.constants import ChatType
from services_veretevo.notification_service import NotificationService


def register_menu_handlers(application: Application) -> None:
    """
    Регистрирует обработчики команд меню в приложении Telegram.

    Args:
        application (Application): Экземпляр Telegram Application.
    """
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Главное меню$"), go_main_menu))
    application.add_handler(MessageHandler(filters.Regex("Помощь"), help_command))
    application.add_handler(MessageHandler(filters.Regex("^Помощь$"), help_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, auto_add_member))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, auto_remove_member))
    application.add_handler(CommandHandler("set_department", set_department))
    application.add_handler(CommandHandler("sync_members", sync_members))
    application.add_handler(CommandHandler("notify_update", notify_update))
    application.add_handler(CommandHandler("notify_all", notify_all))


async def go_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет главное меню пользователю. В группах — только текст, в личке — с клавиатурой.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    chat_type = update.effective_chat.type if update.effective_chat else "private"
    user_id = update.effective_user.id if update.effective_user else None
    if chat_type == "private":
        reply_markup = main_menu_keyboard(chat_type, user_id)
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardRemove())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start. Показывает приветствие и главное меню только в личных чатах.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    logging.debug("start вызван")
    chat_type = update.effective_chat.type if update.effective_chat else "private"
    if chat_type != "private":
        await update.message.reply_text("Для работы с ботом используйте личный чат!", reply_markup=ReplyKeyboardRemove())
        return  # Не реагируем на /start в группах
    
    user = update.effective_user
    user_id = user.id if user else None
    
    # Регистрируем пользователя в системе уведомлений
    if user_id and hasattr(context, 'bot') and context.bot:
        try:
            notification_service = NotificationService(context.bot)
            notification_service.register_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        except Exception as e:
            logging.error(f"[NOTIFICATION] Ошибка регистрации пользователя {user_id}: {e}")
    
    reply_markup = main_menu_keyboard(chat_type, user_id)
    await update.message.reply_text(
        "Привет! Я TaskBot.\n\nВыберите действие:",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет справку по функциям бота. Для директора — расширенная справка.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
    """
    logging.debug("help_command вызван")
    user_id = update.effective_user.id if update.effective_user else None
    if user_id == GENERAL_DIRECTOR_ID:
        text = (
            "🛠️ <b>Административные команды</b>\n"
            "/add_member <b>отдел</b> <b>user_id</b> <b>Имя</b> — добавить участника в отдел\n"
            "/remove_member <b>отдел</b> <b>user_id</b> — удалить участника из отдела\n"
            "/list_members <b>отдел</b> — показать участников отдела\n"
            "/set_department <b>отдел</b> — привязать этот групповой чат к отделу (для авто-добавления участников)\n"
            "\n<b>Пример:</b>\n"
            "/add_member assistants 123456789 Иван Иванов\n"
            "/remove_member finance 123456789\n"
            "/list_members assistants\n"
            "/set_department carpenters\n"
            "\n<b>Основные функции:</b>\n"
            "- 📌 Новая задача — создать задачу\n"
            "- 📋 Список задач — посмотреть задачи отдела\n"
            "- Мои задачи — ваши личные задачи\n"
            "\n<b>Автоматизация:</b>\n"
            "- Если бот добавлен в групповой чат отдела, новые участники автоматически становятся членами отдела.\n"
            "- Для этого чат должен быть привязан к отделу через /set_department.\n"
        )
    else:
        text = (
            "<b>Основные функции:</b>\n"
            "- 📌 Новая задача — создать задачу\n"
            "- 📋 Список задач — посмотреть задачи отдела\n"
            "- Мои задачи — ваши личные задачи\n"
        )
    if update.effective_chat and update.effective_chat.type == "private":
        reply_markup = main_menu_keyboard("private", user_id)
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())


async def auto_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or not chat.id:
        return
    # Найти отдел по chat_id
    department = None
    for dep_key, dep in department_service.DEPARTMENTS.items():
        if dep.get("chat_id") == chat.id:
            department = dep
            department_key = dep_key
            break
    if not department:
        return
    for member in update.message.new_chat_members:
        user_id = str(member.id)
        name = member.full_name or member.username or f"user_{user_id}"
        if user_id not in department["members"]:
            department["members"][user_id] = name
            department_service.save_departments()
            logging.info(f"[AUTO-ADD] {name} ({user_id}) добавлен в отдел {department['name']}")

async def auto_remove_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or not chat.id:
        return
    department = None
    for dep_key, dep in department_service.DEPARTMENTS.items():
        if dep.get("chat_id") == chat.id:
            department = dep
            department_key = dep_key
            break
    if not department:
        return
    left_member = update.message.left_chat_member
    if left_member:
        user_id = str(left_member.id)
        if user_id in department["members"]:
            name = department["members"].pop(user_id)
            department_service.save_departments()
            logging.info(f"[AUTO-REMOVE] {name} ({user_id}) удалён из отдела {department['name']}")

async def set_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id != GENERAL_DIRECTOR_ID:
        await update.message.reply_text("Только генеральный директор может выполнять эту команду.")
        return
    chat = update.effective_chat
    if not chat or chat.type == "private":
        await update.message.reply_text("Эту команду можно использовать только в групповых чатах.")
        return
    args = context.args if hasattr(context, 'args') else []
    if not args or len(args) < 1:
        await update.message.reply_text("Укажите ключ отдела. Пример: /set_department finance")
        return
    dep_key = args[0]
    if dep_key not in department_service.DEPARTMENTS:
        await update.message.reply_text(f"Отдел '{dep_key}' не найден.")
        return
    department_service.DEPARTMENTS[dep_key]["chat_id"] = chat.id
    department_service.save_departments()
    await update.message.reply_text(f"Чат успешно привязан к отделу '{department_service.DEPARTMENTS[dep_key]['name']}'. Теперь новые участники будут автоматически добавляться в отдел.")

async def sync_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id != GENERAL_DIRECTOR_ID:
        await update.message.reply_text("Только генеральный директор может выполнять эту команду.")
        return
    args = context.args if hasattr(context, 'args') else []
    if not args or len(args) < 1:
        await update.message.reply_text("Укажите ключ отдела. Пример: /sync_members assistants")
        return
    dep_key = args[0]
    dep = department_service.DEPARTMENTS.get(dep_key)
    if not dep:
        await update.message.reply_text(f"Отдел '{dep_key}' не найден.")
        return
    chat_id = dep.get("chat_id")
    if not chat_id:
        await update.message.reply_text("Для отдела не привязан групповой чат.")
        return
    try:
        chat = await context.bot.get_chat(chat_id)
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await update.message.reply_text("Привязанный чат не является группой.")
            return
        # Получаем список админов (getChatAdministrators) и всех участников (getChatMemberCount)
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = {str(admin.user.id): admin.user.full_name or admin.user.username or f"user_{admin.user.id}" for admin in admins}
        # Получаем количество участников
        count = await context.bot.get_chat_member_count(chat_id)
        # ВНИМАНИЕ: Telegram Bot API не позволяет получить полный список участников, только админов и по одному через getChatMember
        # Поэтому синхронизируем только админов (или, если нужно, можно реализовать перебор по user_id, если они известны)
        dep["members"] = admin_ids
        department_service.save_departments()
        await update.message.reply_text(f"Синхронизировано! Теперь в отделе {dep['name']} {len(admin_ids)} админ(ов) из группы (всего участников: {count}).")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при синхронизации: {e}")

async def notify_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет уведомление об обновлении бота всем пользователям"""
    user_id = update.effective_user.id if update.effective_user else None
    if user_id != GENERAL_DIRECTOR_ID:
        await update.message.reply_text("Только генеральный директор может выполнять эту команду.")
        return
    
    args = context.args if hasattr(context, 'args') else []
    if len(args) < 2:
        await update.message.reply_text(
            "Использование: /notify_update <заголовок> <описание>\n"
            "Пример: /notify_update \"Обновление меню\" \"Добавлены новые функции в главное меню\""
        )
        return
    
    title = args[0]
    description = " ".join(args[1:])
    
    try:
        notification_service = NotificationService(context.bot)
        notification_id = await notification_service.send_update_notification(title, description)
        await update.message.reply_text(
            f"✅ Уведомление об обновлении отправлено всем пользователям (ID: {notification_id})"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки уведомления: {e}")

async def notify_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет произвольное уведомление всем пользователям"""
    user_id = update.effective_user.id if update.effective_user else None
    if user_id != GENERAL_DIRECTOR_ID:
        await update.message.reply_text("Только генеральный директор может выполнять эту команду.")
        return
    
    args = context.args if hasattr(context, 'args') else []
    if len(args) < 2:
        await update.message.reply_text(
            "Использование: /notify_all <заголовок> <сообщение>\n"
            "Пример: /notify_all \"Важное сообщение\" \"Плановые работы в воскресенье\""
        )
        return
    
    title = args[0]
    message = " ".join(args[1:])
    
    try:
        notification_service = NotificationService(context.bot)
        notification_id = notification_service.create_notification(
            title=title,
            message=message,
            notification_type="announcement"
        )
        await notification_service.send_notification_to_all(notification_id)
        await update.message.reply_text(
            f"✅ Уведомление отправлено всем пользователям (ID: {notification_id})"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки уведомления: {e}")