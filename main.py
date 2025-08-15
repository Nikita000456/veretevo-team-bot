import time
import socket
import os
import logging
import asyncio
import datetime
import pytz
from telegram.ext import ApplicationBuilder
from config_veretevo.env import TELEGRAM_TOKEN
from config_veretevo.constants import VERSION
from handlers_veretevo.menu import register_menu_handlers
from handlers_veretevo.tasks import register_task_handlers
from handlers_veretevo.reports import register_report_handlers, send_morning_report, send_evening_report
from handlers_veretevo.gpt_handlers import register_gpt_handlers
from handlers_veretevo.voice_handler import register_voice_handlers
from handlers_veretevo.contacts import register_contacts_handlers
from services_veretevo.department_service import load_departments, DEPARTMENTS
import requests
from config_veretevo.constants import GENERAL_DIRECTOR_ID
import threading
from utils_veretevo.todoist_sync_polling import sync_todoist_to_bot
from utils_veretevo.group_monitor import GroupMonitor
import json

# Устанавливаем часовой пояс для московского времени
os.environ['TZ'] = 'Europe/Moscow'

# Настройки для единственного режима работы
LOGS_DIR = "logs"
TASKS_FILE = "data/tasks.json"

# Глобальная переменная для отслеживания отправки уведомления о запуске
_notify_start_called = False

def notify_start():
    global _notify_start_called
    
    # Проверяем, было ли уже отправлено уведомление
    if _notify_start_called:
        print(f"[WARN] notify_start() уже была вызвана, пропускаем")
        logging.info(f"[WARN] notify_start() уже была вызвана, пропускаем")
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        call_time = time.time()
        hostname = socket.gethostname()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"Veretevo Bot v{VERSION} был запущен/перезапущен на сервере!\n\n🆔 ID: {call_time}\n🖥️ Host: {hostname}\n⏰ Time: {timestamp}"
        print(f"[INFO] Отправка уведомления о запуске в {GENERAL_DIRECTOR_ID}")
        logging.info(f"[INFO] Отправка уведомления о запуске в {GENERAL_DIRECTOR_ID}")
        response = requests.post(url, data={"chat_id": GENERAL_DIRECTOR_ID, "text": msg}, timeout=5)
        print(f"[INFO] Уведомление отправлено, статус: {response.status_code}")
        logging.info(f"[INFO] Уведомление отправлено, статус: {response.status_code}")
        
        # Отмечаем, что уведомление было отправлено
        _notify_start_called = True
        
    except Exception as e:
        print(f"[WARN] Не удалось отправить уведомление в Telegram: {e}")
        logging.info(f"[WARN] Не удалось отправить уведомление в Telegram: {e}")
        # Не пытаемся повторно отправить, так как это может вызвать бесконечный цикл ошибок

def periodic_todoist_sync(application=None):
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except Exception:
        tasks = []
    
    # Запускаем синхронизацию в отдельном потоке, чтобы не блокировать основной поток
    def sync_worker():
        try:
            sync_todoist_to_bot(tasks, GENERAL_DIRECTOR_ID, application)
            # Сохраняем только если синхронизация прошла успешно
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Ошибка синхронизации с Todoist: {e}")
    
    # Запускаем синхронизацию в фоне
    sync_thread = threading.Thread(target=sync_worker, daemon=True)
    sync_thread.start()
    
    # Запускаем снова через 5 минут
    threading.Timer(300, lambda: periodic_todoist_sync(application)).start()

def setup_logging():
    """Настройка логирования"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(f"{LOGS_DIR}/bot.log", encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers = []  # Убираем все старые хендлеры
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

def run_async_report(report_func):
    """Обертка для запуска асинхронных функций отчетов"""
    try:
        if application and application.bot:
            # Используем asyncio.create_task для запуска в существующем event loop
            import asyncio
            try:
                # Пытаемся получить текущий event loop
                loop = asyncio.get_running_loop()
                # Создаем задачу в текущем loop
                task = loop.create_task(report_func(application.bot))
                logging.info(f"✅ Задача отчета {report_func.__name__} создана в текущем event loop")
            except RuntimeError:
                # Если нет запущенного loop, создаем новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(report_func(application.bot))
                loop.close()
                logging.info(f"✅ Отчет {report_func.__name__} выполнен в новом event loop")
        else:
            logging.error(f"❌ Не удалось выполнить отчет {report_func.__name__}: application.bot недоступен")
    except Exception as e:
        logging.error(f"❌ Ошибка выполнения отчета {report_func.__name__}: {e}", exc_info=True)

def setup_report_scheduler(application):
    """Настройка планировщика отчетов"""
    try:
        # Проверяем, что job_queue доступен
        if not application or not application.job_queue:
            logging.error("❌ JobQueue недоступен для настройки планировщика отчетов")
            print("❌ JobQueue недоступен для настройки планировщика отчетов")
            return
        
        # Создаем московский часовой пояс
        moscow_tz = pytz.timezone('Europe/Moscow')
        
        # Конвертируем московское время в UTC
        # 7:30 МСК = 4:30 UTC (зимой) или 4:30 UTC (летом)
        # 18:00 МСК = 15:00 UTC (зимой) или 15:00 UTC (летом)
        
        # Утренний отчет в 7:30 по московскому времени (4:30 UTC)
        morning_time_utc = datetime.time(hour=4, minute=30)
        
        application.job_queue.run_daily(
            lambda context: run_async_report(send_morning_report), 
            time=morning_time_utc,
            days=(0, 1, 2, 3, 4, 5, 6)  # Все дни недели
        )
        
        # Вечерний отчет в 18:00 по московскому времени (15:00 UTC)
        evening_time_utc = datetime.time(hour=15, minute=0)
        
        application.job_queue.run_daily(
            lambda context: run_async_report(send_evening_report), 
            time=evening_time_utc,
            days=(0, 1, 2, 3, 4, 5, 6)  # Все дни недели
        )
        
        logging.info("✅ Планировщик отчетов настроен: утренний в 7:30 MSK (4:30 UTC), вечерний в 18:00 MSK (15:00 UTC)")
        print("✅ Планировщик отчетов настроен: утренний в 7:30 MSK (4:30 UTC), вечерний в 18:00 MSK (15:00 UTC)")
        
    except Exception as e:
        logging.error(f"❌ Ошибка настройки планировщика отчетов: {e}")
        print(f"❌ Ошибка настройки планировщика отчетов: {e}")

def main():
    global application
    
    print("=== Veretevo Bot запускается ===")
    print(f"Версия бота: {VERSION}")
    
    # Быстрая настройка логирования
    setup_logging()
    logging.info("=== Veretevo Bot успешно запущен (перезапущен) ===")
    
    # Загружаем отделы в фоне
    print("Загрузка отделов...")
    load_departments()
    
    # Создаем application с job_queue
    print("Инициализация Telegram бота...")
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не установлен")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Глобальный error handler
    async def error_handler(update, context):
        logging.error(f"[ERROR] Exception: {context.error}", exc_info=context.error)
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")

    application.add_error_handler(error_handler)

    # Регистрация обработчиков
    print("Регистрация обработчиков...")
    register_gpt_handlers(application)  # GPT-обработчики первыми
    register_menu_handlers(application)
    register_task_handlers(application)
    register_report_handlers(application)
    register_voice_handlers(application)  # Голосовые сообщения для всех чатов
    register_contacts_handlers(application)  # Обработчики команд по контактам

    # Настройка планировщика отчетов
    print("Настройка планировщика отчетов...")
    
    # Пытаемся настроить планировщик с задержкой
    def setup_scheduler_with_retry():
        import time
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                setup_report_scheduler(application)
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Попытка {attempt + 1} настройки планировщика не удалась, повтор через 2 секунды...")
                    time.sleep(2)
                else:
                    print(f"Не удалось настроить планировщик после {max_attempts} попыток")
    
    # Запускаем настройку планировщика в отдельном потоке
    import threading
    scheduler_thread = threading.Thread(target=setup_scheduler_with_retry, daemon=True)
    scheduler_thread.start()

    # Запуск системы мониторинга групп
    print("Запуск системы мониторинга групп...")
    
    # Настройка уведомлений (можно отключить через переменную окружения)
    enable_notifications = os.getenv("ENABLE_GROUP_NOTIFICATIONS", "true").lower() == "true"
    group_monitor = GroupMonitor(enable_notifications=enable_notifications)
    
    # Запускаем мониторинг в отдельном потоке
    def start_monitoring():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(group_monitor.start_monitoring(application))
    
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    
    if enable_notifications:
        print("✅ Уведомления о изменениях в группах включены")
    else:
        print("🔇 Уведомления о изменениях в группах отключены")

    # Отправляем уведомление о запуске
    print("Отправка уведомления о запуске...")
    notify_start()
    
    # Запуск периодической синхронизации с Todoist (в фоне)
    print("Запуск периодической синхронизации...")
    periodic_todoist_sync(application)

    print("=== Veretevo Bot готов к работе ===")
    application.run_polling()

if __name__ == "__main__":
    main()
