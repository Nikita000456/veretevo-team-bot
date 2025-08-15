import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
from telegram import Bot
from config_veretevo.constants import GENERAL_DIRECTOR_ID

class NotificationService:
    """Сервис для автоматических уведомлений пользователей"""
    
    def __init__(self, bot: Bot, data_dir: str = "data"):
        self.bot = bot
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "active_users.json")
        self.notifications_file = os.path.join(data_dir, "notifications.json")
        self._load_data()
    
    def _load_data(self):
        """Загружает данные о пользователях и уведомлениях"""
        # Загружаем активных пользователей
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.active_users = json.load(f)
        except FileNotFoundError:
            self.active_users = {"users": {}, "last_updated": datetime.now().isoformat()}
        
        # Загружаем историю уведомлений
        try:
            with open(self.notifications_file, 'r', encoding='utf-8') as f:
                self.notifications = json.load(f)
        except FileNotFoundError:
            self.notifications = {"notifications": [], "last_id": 0}
    
    def _save_data(self):
        """Сохраняет данные о пользователях и уведомлениях"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.active_users, f, ensure_ascii=False, indent=2)
        
        with open(self.notifications_file, 'w', encoding='utf-8') as f:
            json.dump(self.notifications, f, ensure_ascii=False, indent=2)
    
    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Регистрирует активного пользователя"""
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()
        
        if user_id_str not in self.active_users["users"]:
            self.active_users["users"][user_id_str] = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "registered_at": current_time,
                "last_activity": current_time,
                "notifications_enabled": True
            }
        else:
            # Обновляем время последней активности
            self.active_users["users"][user_id_str]["last_activity"] = current_time
            if username:
                self.active_users["users"][user_id_str]["username"] = username
            if first_name:
                self.active_users["users"][user_id_str]["first_name"] = first_name
            if last_name:
                self.active_users["users"][user_id_str]["last_name"] = last_name
        
        self.active_users["last_updated"] = current_time
        self._save_data()
        logging.info(f"[NOTIFICATION] Зарегистрирован пользователь {user_id}")
    
    def create_notification(self, title: str, message: str, notification_type: str = "update", 
                          requires_action: bool = False, action_text: str = None) -> int:
        """Создает новое уведомление"""
        notification_id = self.notifications["last_id"] + 1
        self.notifications["last_id"] = notification_id
        
        notification = {
            "id": notification_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "requires_action": requires_action,
            "action_text": action_text,
            "created_at": datetime.now().isoformat(),
            "sent_to": []
        }
        
        self.notifications["notifications"].append(notification)
        self._save_data()
        
        logging.info(f"[NOTIFICATION] Создано уведомление #{notification_id}: {title}")
        return notification_id
    
    async def send_notification_to_all(self, notification_id: int, exclude_users: List[int] = None):
        """Отправляет уведомление всем активным пользователям"""
        if exclude_users is None:
            exclude_users = []
        
        notification = None
        for n in self.notifications["notifications"]:
            if n["id"] == notification_id:
                notification = n
                break
        
        if not notification:
            logging.error(f"[NOTIFICATION] Уведомление #{notification_id} не найдено")
            return
        
        exclude_users_str = [str(uid) for uid in exclude_users]
        success_count = 0
        error_count = 0
        
        for user_id_str, user_data in self.active_users["users"].items():
            if user_id_str in exclude_users_str:
                continue
            
            if not user_data.get("notifications_enabled", True):
                continue
            
            try:
                # Формируем сообщение
                text = f"🔔 <b>{notification['title']}</b>\n\n{notification['message']}"
                
                if notification["requires_action"] and notification["action_text"]:
                    text += f"\n\n{notification['action_text']}"
                
                await self.bot.send_message(
                    chat_id=user_data["user_id"],
                    text=text,
                    parse_mode="HTML"
                )
                
                # Отмечаем, что уведомление отправлено
                if user_data["user_id"] not in notification["sent_to"]:
                    notification["sent_to"].append(user_data["user_id"])
                
                success_count += 1
                logging.debug(f"[NOTIFICATION] Уведомление #{notification_id} отправлено пользователю {user_data['user_id']}")
                
                # Небольшая задержка между отправками
                await asyncio.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                logging.error(f"[NOTIFICATION] Ошибка отправки уведомления #{notification_id} пользователю {user_data['user_id']}: {e}")
        
        self._save_data()
        logging.info(f"[NOTIFICATION] Уведомление #{notification_id} отправлено: успешно {success_count}, ошибок {error_count}")
    
    async def send_update_notification(self, update_title: str, update_description: str):
        """Отправляет уведомление об обновлении бота"""
        notification_id = self.create_notification(
            title=update_title,
            message=update_description,
            notification_type="update",
            requires_action=True,
            action_text="Отправьте /start для обновления меню"
        )
        
        await self.send_notification_to_all(notification_id)
        return notification_id
    
    def get_active_users_count(self) -> int:
        """Возвращает количество активных пользователей"""
        return len(self.active_users["users"])
    
    def get_recent_users(self, days: int = 7) -> List[Dict]:
        """Возвращает пользователей, активных за последние N дней"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_users = []
        
        for user_data in self.active_users["users"].values():
            last_activity = datetime.fromisoformat(user_data["last_activity"])
            if last_activity > cutoff_date:
                recent_users.append(user_data)
        
        return recent_users
    
    def cleanup_inactive_users(self, days: int = 30):
        """Удаляет неактивных пользователей"""
        cutoff_date = datetime.now() - timedelta(days=days)
        users_to_remove = []
        
        for user_id_str, user_data in self.active_users["users"].items():
            last_activity = datetime.fromisoformat(user_data["last_activity"])
            if last_activity < cutoff_date:
                users_to_remove.append(user_id_str)
        
        for user_id_str in users_to_remove:
            del self.active_users["users"][user_id_str]
        
        if users_to_remove:
            self._save_data()
            logging.info(f"[NOTIFICATION] Удалено {len(users_to_remove)} неактивных пользователей")
        
        return len(users_to_remove) 