"""
Система автоматического мониторинга событий в группах.
Отслеживает добавление/удаление участников и автоматически обновляет конфигурацию отделов.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from telegram import Update, Bot, ChatMemberUpdated, ChatMember
from telegram.ext import Application, ContextTypes
from telegram.error import TelegramError, Forbidden
from config_veretevo.env import TELEGRAM_TOKEN
from services_veretevo.department_service import load_departments, save_departments, DEPARTMENTS
from config_veretevo.constants import DEPARTMENTS_JSON_PATH

logger = logging.getLogger(__name__)

class GroupMonitor:
    """Класс для мониторинга событий в группах и автоматического обновления конфигурации"""
    
    def __init__(self, token: str = None, enable_notifications: bool = True):
        """
        Инициализация монитора групп
        
        Args:
            token (str): Токен бота. Если не указан, используется из env
            enable_notifications (bool): Включить уведомления о изменениях
        """
        self.token = token or TELEGRAM_TOKEN
        if not self.token:
            raise ValueError("Токен Telegram бота не найден")
        self.bot = Bot(token=self.token)
        self.monitored_chats: Set[int] = set()
        self.enable_notifications = enable_notifications
        self.load_monitored_chats()
    
    def load_monitored_chats(self):
        """Загружает список отслеживаемых чатов из конфигурации отделов"""
        load_departments()
        for department in DEPARTMENTS.values():
            chat_id = department.get("chat_id")
            if chat_id:
                self.monitored_chats.add(chat_id)
        logger.info(f"Загружено {len(self.monitored_chats)} отслеживаемых чатов")
    
    async def handle_chat_member_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает обновления участников чата
        
        Args:
            update (Update): Объект обновления Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст выполнения
        """
        if not update.chat_member:
            return
        
        chat_member_update: ChatMemberUpdated = update.chat_member
        chat_id = chat_member_update.chat.id
        
        # Проверяем, отслеживается ли этот чат
        if chat_id not in self.monitored_chats:
            return
        
        # Получаем информацию об отделе
        department_key = self.get_department_by_chat_id(chat_id)
        if not department_key:
            logger.warning(f"Чат {chat_id} не найден в конфигурации отделов")
            return
        
        old_member = chat_member_update.old_chat_member
        new_member = chat_member_update.new_chat_member
        user = chat_member_update.from_user
        
        # Определяем тип события
        event_type = self.determine_event_type(old_member, new_member)
        
        if event_type == "added":
            await self.handle_member_added(department_key, user)
        elif event_type == "removed":
            await self.handle_member_removed(department_key, user)
        elif event_type == "promoted":
            await self.handle_member_promoted(department_key, user)
        elif event_type == "demoted":
            await self.handle_member_demoted(department_key, user)
    
    def determine_event_type(self, old_member: ChatMember, new_member: ChatMember) -> str:
        """
        Определяет тип события с участником
        
        Args:
            old_member (ChatMember): Старый статус участника
            new_member (ChatMember): Новый статус участника
            
        Returns:
            str: Тип события ('added', 'removed', 'promoted', 'demoted', 'none')
        """
        old_status = old_member.status
        new_status = new_member.status
        
        # Участник добавлен
        if old_status == "left" and new_status in ["member", "administrator", "creator"]:
            return "added"
        
        # Участник удален
        if old_status in ["member", "administrator", "creator"] and new_status == "left":
            return "removed"
        
        # Участник повышен до администратора
        if old_status == "member" and new_status == "administrator":
            return "promoted"
        
        # Участник понижен с администратора
        if old_status == "administrator" and new_status == "member":
            return "demoted"
        
        return "none"
    
    def get_department_by_chat_id(self, chat_id: int) -> Optional[str]:
        """
        Находит отдел по ID чата
        
        Args:
            chat_id (int): ID чата
            
        Returns:
            Optional[str]: Ключ отдела или None
        """
        load_departments()
        for key, department in DEPARTMENTS.items():
            if department.get("chat_id") == chat_id:
                return key
        return None
    
    async def handle_member_added(self, department_key: str, user):
        """
        Обрабатывает добавление участника
        
        Args:
            department_key (str): Ключ отдела
            user: Объект пользователя
        """
        try:
            load_departments()
            department = DEPARTMENTS[department_key]
            user_id_str = str(user.id)
            user_name = user.username or user.first_name or f"User{user.id}"
            
            # Добавляем участника в конфигурацию
            department["members"][user_id_str] = user_name
            save_departments()
            
            logger.info(f"✅ Автоматически добавлен участник {user_name} (ID: {user.id}) в отдел '{department_key}'")
            
            # Отправляем уведомление администраторам (если включено)
            if self.enable_notifications:
                await self.notify_admins(department_key, f"👤 Добавлен новый участник: {user_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении участника {user.id} в отдел {department_key}: {e}")
    
    async def handle_member_removed(self, department_key: str, user):
        """
        Обрабатывает удаление участника
        
        Args:
            department_key (str): Ключ отдела
            user: Объект пользователя
        """
        try:
            load_departments()
            department = DEPARTMENTS[department_key]
            user_id_str = str(user.id)
            
            if user_id_str in department["members"]:
                user_name = department["members"][user_id_str]
                del department["members"][user_id_str]
                save_departments()
                
                logger.info(f"❌ Автоматически удален участник {user_name} (ID: {user.id}) из отдела '{department_key}'")
                
                # Отправляем уведомление администраторам (если включено)
                if self.enable_notifications:
                    await self.notify_admins(department_key, f"👤 Удален участник: {user_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при удалении участника {user.id} из отдела {department_key}: {e}")
    
    async def handle_member_promoted(self, department_key: str, user):
        """
        Обрабатывает повышение участника до администратора
        
        Args:
            department_key (str): Ключ отдела
            user: Объект пользователя
        """
        try:
            user_name = user.username or user.first_name or f"User{user.id}"
            logger.info(f"⭐ Участник {user_name} (ID: {user.id}) повышен до администратора в отделе '{department_key}'")
            
            # Отправляем уведомление администраторам (если включено)
            if self.enable_notifications:
                await self.notify_admins(department_key, f"⭐ {user_name} повышен до администратора")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке повышения участника {user.id} в отделе {department_key}: {e}")
    
    async def handle_member_demoted(self, department_key: str, user):
        """
        Обрабатывает понижение администратора
        
        Args:
            department_key (str): Ключ отдела
            user: Объект пользователя
        """
        try:
            user_name = user.username or user.first_name or f"User{user.id}"
            logger.info(f"📉 Администратор {user_name} (ID: {user.id}) понижен в отделе '{department_key}'")
            
            # Отправляем уведомление администраторам (если включено)
            if self.enable_notifications:
                await self.notify_admins(department_key, f"📉 {user_name} понижен с администратора")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке понижения участника {user.id} в отделе {department_key}: {e}")
    
    async def notify_admins(self, department_key: str, message: str):
        """
        Отправляет уведомление администраторам отдела
        
        Args:
            department_key (str): Ключ отдела
            message (str): Сообщение для отправки
        """
        try:
            load_departments()
            department = DEPARTMENTS[department_key]
            chat_id = department.get("chat_id")
            
            if not chat_id:
                return
            
            # Отправляем уведомление в группу
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"🔄 **Автоматическое обновление отдела**\n{message}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления в отдел {department_key}: {e}")
    
    async def start_monitoring(self, application: Application):
        """
        Запускает мониторинг групп
        
        Args:
            application (Application): Экземпляр приложения Telegram
        """
        # Регистрируем обработчик событий участников
        application.add_handler(
            ChatMemberHandler(self.handle_chat_member_update)
        )
        
        logger.info("🚀 Мониторинг групп запущен")
        
        # Убираем уведомление о запуске - оно может быть навязчивым
        # await self.notify_all_departments("🟢 Система автоматического мониторинга участников запущена")
    
    async def notify_all_departments(self, message: str):
        """
        Отправляет уведомление во все отделы
        
        Args:
            message (str): Сообщение для отправки
        """
        load_departments()
        for department_key, department in DEPARTMENTS.items():
            chat_id = department.get("chat_id")
            if chat_id:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"📢 **Системное уведомление**\n{message}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления в отдел {department_key}: {e}")

# Импорт для обработчика событий
from telegram.ext import ChatMemberHandler 