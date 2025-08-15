"""
Расширенный модуль для работы с задачами.
Добавляет функциональность: приоритеты, теги, категории, напоминания.
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

class Priority(Enum):
    """Приоритеты задач"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskCategory(Enum):
    """Категории задач"""
    DEVELOPMENT = "development"
    DESIGN = "design"
    MARKETING = "marketing"
    ADMINISTRATION = "administration"
    SUPPORT = "support"
    PLANNING = "planning"
    OTHER = "other"

@dataclass
class TaskTag:
    """Тег задачи"""
    name: str
    color: str = "#007bff"  # Синий по умолчанию

@dataclass
class TaskReminder:
    """Напоминание о задаче"""
    task_id: int
    reminder_time: datetime
    message: str
    is_sent: bool = False

class EnhancedTaskService:
    """Расширенный сервис для работы с задачами"""
    
    def __init__(self):
        self.priority_keywords = {
            Priority.URGENT: ["срочно", "urgent", "критично", "немедленно", "asap", "🔥", "⚡"],
            Priority.HIGH: ["важно", "important", "высокий", "приоритет", "❗", "⚠️"],
            Priority.MEDIUM: ["обычно", "normal", "средний", "📋"],
            Priority.LOW: ["неважно", "low", "низкий", "📝"]
        }
        
        self.category_keywords = {
            TaskCategory.DEVELOPMENT: ["код", "программирование", "разработка", "bug", "feature", "dev", "💻"],
            TaskCategory.DESIGN: ["дизайн", "design", "ui", "ux", "макет", "🎨"],
            TaskCategory.MARKETING: ["маркетинг", "marketing", "реклама", "продвижение", "📢"],
            TaskCategory.ADMINISTRATION: ["админ", "admin", "управление", "настройка", "⚙️"],
            TaskCategory.SUPPORT: ["поддержка", "support", "помощь", "help", "🆘"],
            TaskCategory.PLANNING: ["планирование", "planning", "планы", "стратегия", "📅"],
        }
        
        self.reminders: List[TaskReminder] = []
        self.tags: Dict[str, TaskTag] = {}
    
    def detect_priority(self, text: str) -> Priority:
        """Автоматически определяет приоритет задачи на основе текста"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return priority
        
        return Priority.MEDIUM  # По умолчанию средний приоритет
    
    def detect_category(self, text: str) -> TaskCategory:
        """Автоматически определяет категорию задачи"""
        text_lower = text.lower()
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return TaskCategory.OTHER
    
    def extract_tags(self, text: str) -> List[str]:
        """Извлекает теги из текста задачи (слова с #)"""
        tags = re.findall(r'#(\w+)', text)
        return list(set(tags))  # Убираем дубликаты
    
    def create_enhanced_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создает задачу с расширенными полями"""
        text = task_data.get('text', '')
        
        enhanced_task = task_data.copy()
        enhanced_task.update({
            'priority': self.detect_priority(text).value,
            'category': self.detect_category(text).value,
            'tags': self.extract_tags(text),
            'created_at': datetime.now().isoformat(),
            'reminders': [],
            'comments': [],
            'estimated_time': None,  # Время в часах
            'actual_time': None,     # Фактическое время
            'deadline': None,        # Дедлайн
            'progress': 0,           # Прогресс в процентах
        })
        
        return enhanced_task
    
    def add_comment(self, task_id: int, user_id: int, user_name: str, comment: str) -> bool:
        """Добавляет комментарий к задаче"""
        from services_veretevo.task_service import get_task_by_id, save_tasks
        
        task = get_task_by_id(task_id)
        if not task:
            return False
        
        comment_data = {
            'id': len(task.get('comments', [])) + 1,
            'user_id': user_id,
            'user_name': user_name,
            'text': comment,
            'created_at': datetime.now().isoformat()
        }
        
        if 'comments' not in task:
            task['comments'] = []
        
        task['comments'].append(comment_data)
        
        # Сохраняем изменения
        from services_veretevo.task_service import tasks, save_tasks
        for i, t in enumerate(tasks):
            if t.get('id') == task_id:
                tasks[i] = task
                break
        
        save_tasks()
        return True
    
    def set_reminder(self, task_id: int, reminder_time: datetime, message: str = "") -> bool:
        """Устанавливает напоминание для задачи"""
        reminder = TaskReminder(
            task_id=task_id,
            reminder_time=reminder_time,
            message=message or f"Напоминание о задаче #{task_id}"
        )
        
        self.reminders.append(reminder)
        return True
    
    def get_due_reminders(self) -> List[TaskReminder]:
        """Возвращает напоминания, которые нужно отправить"""
        now = datetime.now()
        due_reminders = []
        
        for reminder in self.reminders:
            if not reminder.is_sent and reminder.reminder_time <= now:
                due_reminders.append(reminder)
        
        return due_reminders
    
    def mark_reminder_sent(self, reminder: TaskReminder):
        """Отмечает напоминание как отправленное"""
        reminder.is_sent = True
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по задачам"""
        from services_veretevo.task_service import get_tasks
        
        tasks = get_tasks()
        
        stats = {
            'total': len(tasks),
            'by_priority': {},
            'by_category': {},
            'by_status': {},
            'overdue': 0,
            'due_today': 0
        }
        
        now = datetime.now()
        
        for task in tasks:
            # Статистика по приоритетам
            priority = task.get('priority', 'medium')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Статистика по категориям
            category = task.get('category', 'other')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Статистика по статусам
            status = task.get('status', 'new')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Просроченные задачи
            deadline = task.get('deadline')
            if deadline:
                try:
                    deadline_dt = datetime.fromisoformat(deadline)
                    if deadline_dt < now and task.get('status') not in ['completed', 'cancelled']:
                        stats['overdue'] += 1
                    elif deadline_dt.date() == now.date():
                        stats['due_today'] += 1
                except:
                    pass
        
        return stats
    
    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Поиск задач по тексту, тегам, категориям"""
        from services_veretevo.task_service import get_tasks
        
        tasks = get_tasks()
        query_lower = query.lower()
        
        results = []
        for task in tasks:
            # Поиск по тексту
            if query_lower in task.get('text', '').lower():
                results.append(task)
                continue
            
            # Поиск по тегам
            tags = task.get('tags', [])
            for tag in tags:
                if query_lower in tag.lower():
                    results.append(task)
                    break
            
            # Поиск по категории
            category = task.get('category', '')
            if query_lower in category.lower():
                results.append(task)
                continue
            
            # Поиск по автору/исполнителю
            author_name = task.get('author_name', '')
            assistant_name = task.get('assistant_name', '')
            if query_lower in author_name.lower() or query_lower in assistant_name.lower():
                results.append(task)
        
        return results

# Глобальный экземпляр сервиса
enhanced_service = EnhancedTaskService() 