#!/usr/bin/env python3
"""
Скрипт для автоматического уведомления пользователей о обновлениях бота
Использование: python scripts/auto_notify.py [update_type] [title] [description]
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_veretevo.env import TELEGRAM_TOKEN
from telegram import Bot
from services_veretevo.notification_service import NotificationService

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def send_update_notification(update_type: str, title: str, description: str):
    """Отправляет уведомление об обновлении"""
    bot = Bot(token=TELEGRAM_TOKEN)
    notification_service = NotificationService(bot)
    
    try:
        if update_type == "update":
            notification_id = await notification_service.send_update_notification(title, description)
            print(f"✅ Уведомление об обновлении отправлено (ID: {notification_id})")
        else:
            notification_id = notification_service.create_notification(
                title=title,
                message=description,
                notification_type=update_type
            )
            await notification_service.send_notification_to_all(notification_id)
            print(f"✅ Уведомление отправлено (ID: {notification_id})")
        
        # Статистика
        active_users = notification_service.get_active_users_count()
        recent_users = len(notification_service.get_recent_users(7))
        print(f"📊 Активных пользователей: {active_users}")
        print(f"📊 Активных за неделю: {recent_users}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
    finally:
        await bot.close()

async def cleanup_inactive_users():
    """Очищает неактивных пользователей"""
    bot = Bot(token=TELEGRAM_TOKEN)
    notification_service = NotificationService(bot)
    
    try:
        removed_count = notification_service.cleanup_inactive_users(30)
        print(f"🧹 Удалено {removed_count} неактивных пользователей")
        
        active_users = notification_service.get_active_users_count()
        print(f"📊 Осталось активных пользователей: {active_users}")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    finally:
        await bot.close()

async def show_statistics():
    """Показывает статистику пользователей"""
    bot = Bot(token=TELEGRAM_TOKEN)
    notification_service = NotificationService(bot)
    
    try:
        active_users = notification_service.get_active_users_count()
        recent_users = len(notification_service.get_recent_users(7))
        recent_30 = len(notification_service.get_recent_users(30))
        
        print("📊 Статистика пользователей:")
        print(f"   Всего активных: {active_users}")
        print(f"   Активных за неделю: {recent_users}")
        print(f"   Активных за месяц: {recent_30}")
        
        # Показываем последних пользователей
        recent_users_data = notification_service.get_recent_users(7)
        if recent_users_data:
            print("\n👥 Последние активные пользователи:")
            for user in recent_users_data[:10]:  # Показываем только первые 10
                name = user.get('first_name', '') or user.get('username', '') or f"user_{user['user_id']}"
                print(f"   - {name} (ID: {user['user_id']})")
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
    finally:
        await bot.close()

def main():
    """Основная функция"""
    setup_logging()
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scripts/auto_notify.py update <заголовок> <описание>")
        print("  python scripts/auto_notify.py cleanup")
        print("  python scripts/auto_notify.py stats")
        print("\nПримеры:")
        print("  python scripts/auto_notify.py update \"Обновление меню\" \"Добавлены новые функции\"")
        print("  python scripts/auto_notify.py cleanup")
        print("  python scripts/auto_notify.py stats")
        return
    
    command = sys.argv[1]
    
    if command == "update":
        if len(sys.argv) < 4:
            print("❌ Для команды update нужны заголовок и описание")
            return
        
        title = sys.argv[2]
        description = " ".join(sys.argv[3:])
        
        print(f"📢 Отправка уведомления об обновлении...")
        print(f"   Заголовок: {title}")
        print(f"   Описание: {description}")
        
        asyncio.run(send_update_notification("update", title, description))
        
    elif command == "cleanup":
        print("🧹 Очистка неактивных пользователей...")
        asyncio.run(cleanup_inactive_users())
        
    elif command == "stats":
        print("📊 Получение статистики...")
        asyncio.run(show_statistics())
        
    else:
        print(f"❌ Неизвестная команда: {command}")

if __name__ == "__main__":
    main() 