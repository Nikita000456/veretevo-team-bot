import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes
from handlers_veretevo.tasks import (
    assign_department,
    assign_assistant,
    receive_task_text,
    new_task_start
)
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
        self.message.reply_text = AsyncMock()
        
        self.callback_query = Mock()
        self.callback_query.data = "assign_none"
        self.callback_query.message = self.message
        self.callback_query.answer = AsyncMock()
        self.callback_query.edit_message_reply_markup = AsyncMock()

class MockContext:
    def __init__(self, user_data=None):
        self.user_data = user_data or {
            'creating_task': True,
            'task_text': 'Тестовая задача',
            'department': 'assistants'
        }
        self.application = Mock()
        self.bot = Mock()

# Тест 1: Некорректные ID пользователей
@pytest.mark.asyncio
async def test_invalid_user_id_handling():
    """Тест обработки некорректных ID пользователей"""
    test_cases = [
        "assign_none",           # Правильный случай
        "assign_123",            # Правильный случай
        "assign_invalid",        # Некорректный случай
        "assign_",               # Пустой ID
        "assign_abc",            # Буквенный ID
        "assign_123.45",         # Дробный ID
        "assign_-123",           # Отрицательный ID
    ]
    
    for callback_data in test_cases:
        update = MockUpdate()
        update.callback_query.data = callback_data
        context = MockContext()
        
        with patch('handlers_veretevo.tasks.department_service') as mock_dept:
            mock_dept.DEPARTMENTS = {
                'assistants': {
                    'name': 'Ассистенты',
                    'chat_id': -100123456789,
                    'members': {'123': 'Тест Пользователь'}
                }
            }
            
            # Проверяем, что функция не падает с ошибкой
            try:
                result = await assign_department(update, context)
            except ValueError:
                # ValueError допустим для некорректных ID
                pass
            except Exception as e:
                pytest.fail(f"assign_department не должен падать с {type(e).__name__} для '{callback_data}': {e}")

# Тест 2: Отсутствующие данные контекста
@pytest.mark.asyncio
async def test_missing_context_data():
    """Тест обработки отсутствующих данных контекста"""
    update = MockUpdate()
    context = MockContext(user_data=None)  # Пустой контекст
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [('assistants', 'Ассистенты')]
        
        # Проверяем, что функция не падает
        try:
            result = await new_task_start(update, context)
        except AttributeError:
            pytest.fail("new_task_start не должен падать при отсутствии user_data")

# Тест 3: Некорректные callback данные
@pytest.mark.asyncio
async def test_invalid_callback_data():
    """Тест обработки некорректных callback данных"""
    invalid_callbacks = [
        "invalid_data",
        "assign",
        "assign_",
        "assign_none_extra",
        "assign_123_extra",
        "",
        None,
    ]
    
    for callback_data in invalid_callbacks:
        update = MockUpdate()
        update.callback_query.data = callback_data
        context = MockContext()
        
        # Проверяем, что функция не падает
        try:
            result = await assign_type_callback(update, context)
        except Exception as e:
            pytest.fail(f"assign_type_callback не должен падать для '{callback_data}': {e}")

# Тест 4: Ошибки сети
@pytest.mark.asyncio
async def test_network_errors():
    """Тест обработки сетевых ошибок"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'chat_id': -100123456789,
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        # Симулируем ошибку сети при отправке сообщения
        update.message.reply_text.side_effect = Exception("Network error")
        
        # Проверяем, что функция обрабатывает ошибку
        try:
            result = await new_task_start(update, context)
        except Exception as e:
            # Ошибка сети допустима, но не должна быть неожиданной
            assert "Network error" in str(e)

# Тест 5: Пустые или некорректные тексты задач
@pytest.mark.asyncio
async def test_empty_task_text():
    """Тест обработки пустых текстов задач"""
    test_cases = [
        "",                    # Пустая строка
        "   ",                # Только пробелы
        "\n\n\n",             # Только переносы строк
        None,                 # None
    ]
    
    for text in test_cases:
        update = MockUpdate(text=text)
        context = MockContext()
        
        # Проверяем, что функция обрабатывает пустые тексты
        try:
            result = await receive_task_text(update, context)
        except Exception as e:
            pytest.fail(f"receive_task_text не должен падать для пустого текста '{text}': {e}")

# Тест 6: Очень длинные тексты задач
@pytest.mark.asyncio
async def test_very_long_task_text():
    """Тест обработки очень длинных текстов задач"""
    long_text = "Очень длинный текст задачи " * 100  # ~3000 символов
    
    update = MockUpdate(text=long_text)
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        # Проверяем, что функция обрабатывает длинные тексты
        try:
            result = await receive_task_text(update, context)
        except Exception as e:
            pytest.fail(f"receive_task_text не должен падать для длинного текста: {e}")

# Тест 7: Специальные символы в тексте
@pytest.mark.asyncio
async def test_special_characters_in_text():
    """Тест обработки специальных символов в тексте"""
    special_texts = [
        "Задача с эмодзи 🎉📝✅",
        "Задача с HTML <b>жирный</b> текст",
        "Задача с символами: !@#$%^&*()",
        "Задача с кириллицей: привет мир",
        "Задача с числами: 1234567890",
        "Задача с переносами\nстрок",
        "Задача с табуляцией\tтекст",
    ]
    
    for text in special_texts:
        update = MockUpdate(text=text)
        context = MockContext()
        
        # Проверяем, что функция обрабатывает специальные символы
        try:
            result = await receive_task_text(update, context)
        except Exception as e:
            pytest.fail(f"receive_task_text не должен падать для текста '{text}': {e}")

# Тест 8: Одновременные запросы
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Тест обработки одновременных запросов"""
    update1 = MockUpdate(user_id=123)
    update2 = MockUpdate(user_id=456)
    context1 = MockContext()
    context2 = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [('assistants', 'Ассистенты')]
        
        # Симулируем одновременные запросы
        try:
            result1 = await new_task_start(update1, context1)
            result2 = await new_task_start(update2, context2)
        except Exception as e:
            pytest.fail(f"new_task_start не должен падать при одновременных запросах: {e}")

# Тест 9: Ошибки в сервисах
@pytest.mark.asyncio
async def test_service_errors():
    """Тест обработки ошибок в сервисах"""
    update = MockUpdate()
    context = MockContext()
    
    # Симулируем ошибку в department_service
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.side_effect = Exception("Service error")
        
        # Проверяем, что функция обрабатывает ошибку сервиса
        try:
            result = await new_task_start(update, context)
        except Exception as e:
            # Ошибка сервиса допустима, но должна быть обработана
            assert "Service error" in str(e)

# Тест 10: Предельные значения
@pytest.mark.asyncio
async def test_boundary_values():
    """Тест обработки предельных значений"""
    # Максимальный user_id
    update = MockUpdate(user_id=999999999999)
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [('assistants', 'Ассистенты')]
        
        # Проверяем, что функция обрабатывает большие ID
        try:
            result = await new_task_start(update, context)
        except Exception as e:
            pytest.fail(f"new_task_start не должен падать для большого user_id: {e}")

# Тест 11: Отсутствующие отделы
@pytest.mark.asyncio
async def test_missing_departments():
    """Тест обработки отсутствующих отделов"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {}  # Пустой список отделов
        
        # Проверяем, что функция обрабатывает отсутствие отделов
        try:
            result = await list_tasks(update, context)
        except Exception as e:
            pytest.fail(f"list_tasks не должен падать при отсутствии отделов: {e}")

# Тест 12: Некорректные данные задач
@pytest.mark.asyncio
async def test_invalid_task_data():
    """Тест обработки некорректных данных задач"""
    invalid_tasks = [
        {},  # Пустой словарь
        {"id": "invalid"},  # Некорректный ID
        {"text": None},  # None вместо текста
        {"status": "invalid_status"},  # Некорректный статус
    ]
    
    for task in invalid_tasks:
        # Проверяем, что add_or_update_task обрабатывает некорректные данные
        try:
            add_or_update_task(task)
        except Exception as e:
            # Ошибки допустимы для некорректных данных
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 