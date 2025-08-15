"""
Модуль для автоматической синхронизации членов Telegram-групп с конфигурацией отделов.
Позволяет получать реальный список участников групп и обновлять конфигурацию.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from telegram import Bot
from telegram.error import TelegramError, Forbidden, BadRequest
from config_veretevo.env import TELEGRAM_TOKEN
from services_veretevo.department_service import load_departments, save_departments, DEPARTMENTS

logger = logging.getLogger(__name__)

class TelegramGroupSync:
    """Класс для синхронизации членов Telegram-групп с конфигурацией отделов"""
    
    def __init__(self, token: str = None):
        """
        Инициализация синхронизатора
        
        Args:
            token (str): Токен бота. Если не указан, используется из env
        """
        self.token = token or TELEGRAM_TOKEN
        if not self.token:
            raise ValueError("Токен Telegram бота не найден")
        self.bot = Bot(token=self.token)
    
    async def initialize(self):
        """Инициализирует бота"""
        await self.bot.initialize()
    
    async def close(self):
        """Закрывает соединение с ботом"""
        await self.bot.close()
    
    async def get_chat_members(self, chat_id: int) -> List[Tuple[int, str]]:
        """
        Получает список участников чата (только администраторов)
        
        Args:
            chat_id (int): ID чата
            
        Returns:
            List[Tuple[int, str]]: Список кортежей (user_id, username/first_name)
        """
        try:
            await self.initialize()
            members = []
            
            # Получаем администраторов (включая владельца)
            try:
                admins = await self.bot.get_chat_administrators(chat_id)
                for member in admins:
                    user = member.user
                    name = user.username or user.first_name or f"User{user.id}"
                    members.append((user.id, name))
                    logger.debug(f"Добавлен администратор: {user.id} - {name}")
            except TelegramError as e:
                logger.warning(f"Не удалось получить администраторов чата {chat_id}: {e}")
            
            # Примечание: Telegram API не предоставляет прямой метод для получения
            # всех участников группы. Получаем только администраторов.
            # Обычные участники должны добавляться вручную в конфигурацию.
                
        except TelegramError as e:
            logger.error(f"Ошибка получения участников чата {chat_id}: {e}")
            return []
        finally:
            await self.close()
        
        # Убираем дубликаты
        unique_members = {}
        for user_id, name in members:
            if user_id not in unique_members:
                unique_members[user_id] = name
        
        logger.info(f"Получено {len(unique_members)} администраторов для чата {chat_id}")
        return list(unique_members.items())
    
    async def sync_department_members(self, department_key: str) -> bool:
        """
        Синхронизирует участников конкретного отдела
        
        Args:
            department_key (str): Ключ отдела
            
        Returns:
            bool: True если синхронизация прошла успешно
        """
        load_departments()
        
        if department_key not in DEPARTMENTS:
            logger.error(f"Отдел {department_key} не найден в конфигурации")
            return False
        
        department = DEPARTMENTS[department_key]
        chat_id = department.get("chat_id")
        
        if not chat_id:
            logger.warning(f"Для отдела {department_key} не указан chat_id")
            return False
        
        try:
            # Получаем реальных участников группы
            real_members = await self.get_chat_members(chat_id)
            
            # Обновляем конфигурацию
            department["members"] = {str(user_id): name for user_id, name in real_members}
            
            # Сохраняем изменения
            save_departments()
            
            logger.info(f"Синхронизирован отдел {department_key}: {len(real_members)} участников")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации отдела {department_key}: {e}")
            return False
    
    async def sync_all_departments(self) -> Dict[str, bool]:
        """
        Синхронизирует все отделы с chat_id
        
        Returns:
            Dict[str, bool]: Результаты синхронизации для каждого отдела
        """
        load_departments()
        results = {}
        
        for department_key, department in DEPARTMENTS.items():
            if department.get("chat_id"):
                results[department_key] = await self.sync_department_members(department_key)
            else:
                logger.info(f"Отдел {department_key} пропущен (нет chat_id)")
                results[department_key] = False
        
        return results
    
    async def get_department_diff(self, department_key: str) -> Dict[str, List]:
        """
        Показывает различия между конфигурацией и реальными участниками группы
        
        Args:
            department_key (str): Ключ отдела
            
        Returns:
            Dict[str, List]: Словарь с различиями
        """
        load_departments()
        
        if department_key not in DEPARTMENTS:
            return {"error": ["Отдел не найден"]}
        
        department = DEPARTMENTS[department_key]
        chat_id = department.get("chat_id")
        
        if not chat_id:
            return {"error": ["Нет chat_id для отдела"]}
        
        # Получаем реальных участников
        real_members = await self.get_chat_members(chat_id)
        real_member_ids = {str(user_id) for user_id, _ in real_members}
        
        # Получаем участников из конфигурации
        config_members = set(department.get("members", {}).keys())
        
        # Находим различия
        missing_in_config = real_member_ids - config_members
        extra_in_config = config_members - real_member_ids
        
        return {
            "missing_in_config": list(missing_in_config),
            "extra_in_config": list(extra_in_config),
            "real_members": real_members,
            "config_members": list(config_members)
        }

async def main_sync():
    """Основная функция для запуска синхронизации"""
    try:
        sync = TelegramGroupSync()
        results = await sync.sync_all_departments()
        
        print("🔄 Результаты синхронизации:")
        for department, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {department}")
            
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main_sync()) 