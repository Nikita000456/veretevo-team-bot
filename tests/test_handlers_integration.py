import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes
from handlers_veretevo.tasks import (
    assign_type_callback, 
    assign_department, 
    assign_assistant,
    receive_task_text,
    new_task_start
)
from services_veretevo.task_service import add_or_update_task
import tempfile
import json
import os

class MockUpdate:
    def __init__(self, user_id=123, chat_id=456, text="Тестовая задача"):
        self.effective_user = Mock()
        self.effective_user.id = user_id
        self.effective_user.full_name = "Тест Пользователь"
        
        self.effective_chat = Mock()
        self.effective_chat.id = chat_id
        self.effective_chat.type = "private"
        
        self.message = Mock()
        self.message.text = text
        
        self.callback_query = Mock()
        self.callback_query.data = "assign_none"
        self.callback_query.message = self.message

class MockContext:
    def __init__(self):
        self.user_data = {
            'creating_task': True,
            'task_text': 'Тестовая задача',
            'department': 'assistants'
        }
        self.application = Mock()
        self.bot = Mock()

def test_assign_type_callback_with_assign_none():
    """Тест обработки 'assign_none' в assign_type_callback"""
    update = MockUpdate()
    context = MockContext()
    
    # Мокаем assign_department
    with patch('handlers_veretevo.tasks.assign_department') as mock_assign:
        mock_assign.return_value = None
        
        # Вызываем функцию
        result = asyncio.run(assign_type_callback(update, context))
        
        # Проверяем, что assign_department был вызван
        mock_assign.assert_called_once()

def test_assign_department_with_assign_none():
    """Тест обработки 'assign_none' в assign_department"""
    update = MockUpdate()
    context = MockContext()
    update.callback_query.data = "assign_none"
    
    # Мокаем необходимые зависимости
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'chat_id': -100123456789,
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        with patch('handlers_veretevo.tasks.add_or_update_task') as mock_add:
            with patch('handlers_veretevo.tasks.send_task_with_media') as mock_send:
                mock_send.return_value = Mock()
                mock_send.return_value.message_id = 999
                
                # Вызываем функцию
                result = asyncio.run(assign_department(update, context))
                
                # Проверяем, что add_or_update_task был вызван без ошибок
                mock_add.assert_called()
                # Проверяем, что не было попытки преобразовать 'none' в int
                assert mock_add.call_args[0][0]['assistant_id'] is None
                assert mock_add.call_args[0][0]['assistant_name'] == "Без назначения"

def test_assign_department_with_invalid_user_id():
    """Тест обработки некорректного ID пользователя"""
    update = MockUpdate()
    context = MockContext()
    update.callback_query.data = "assign_invalid_id"
    
    # Мокаем необходимые зависимости
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'chat_id': -100123456789,
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        # Вызываем функцию и проверяем, что она не падает
        try:
            result = asyncio.run(assign_department(update, context))
        except ValueError:
            pytest.fail("assign_department не должен падать с ValueError")

def test_add_or_update_task_signature():
    """Тест сигнатуры функции add_or_update_task"""
    # Проверяем, что функция принимает только нужные параметры
    import inspect
    from services_veretevo.task_service import add_or_update_task
    
    sig = inspect.signature(add_or_update_task)
    params = list(sig.parameters.keys())
    
    # Функция должна принимать только task
    assert len(params) == 1
    assert 'task' in params

def test_task_creation_flow():
    """Тест полного процесса создания задачи"""
    # Создаем временный файл для тестов
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        test_file = f.name
    
    try:
        # Создаем задачу
        task = {
            "id": 999999,
            "text": "Тестовая задача",
            "status": "новая",
            "author_id": 123,
            "author_name": "Тест Пользователь",
            "assistant_id": None,
            "assistant_name": "Без назначения",
            "department": "assistants",
            "created_at": "2025-07-28T00:00:00",
            "chat_id": 456,
            "history": []
        }
        
        # Проверяем, что add_or_update_task работает без ошибок
        add_or_update_task(task)
        
        # Проверяем, что задача сохранилась
        from services_veretevo.task_service import get_task_by_id
        loaded_task = get_task_by_id(999999)
        assert loaded_task is not None
        assert loaded_task['text'] == "Тестовая задача"
        assert loaded_task['assistant_id'] is None
        assert loaded_task['assistant_name'] == "Без назначения"
        
    finally:
        # Очищаем временный файл
        if os.path.exists(test_file):
            os.unlink(test_file)

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"]) 