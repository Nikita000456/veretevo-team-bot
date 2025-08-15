import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes
from handlers_veretevo.tasks import (
    new_task_start,
    receive_task_text,
    assign_type_callback,
    assign_department,
    assign_assistant,
    cancel_task_callback,
    list_tasks,
    view_personal_tasks
)
from services_veretevo.task_service import add_or_update_task
import tempfile
import json
import os

class MockUpdate:
    def __init__(self, user_id=123, chat_id=456, text="Тестовая задача", chat_type="private"):
        self.effective_user = Mock()
        self.effective_user.id = user_id
        self.effective_user.full_name = "Тест Пользователь"
        
        self.effective_chat = Mock()
        self.effective_chat.id = chat_id
        self.effective_chat.type = chat_type
        
        self.message = Mock()
        self.message.text = text
        self.message.reply_text = AsyncMock()
        self.message.reply_text.return_value = Mock()
        self.message.photo = None  # По умолчанию нет фото
        self.message.document = None
        self.message.video = None
        self.message.audio = None
        self.message.voice = None
        self.message.caption = None
        
        self.callback_query = Mock()
        self.callback_query.data = "assign_none"
        self.callback_query.message = self.message
        self.callback_query.answer = AsyncMock()
        self.callback_query.edit_message_reply_markup = AsyncMock()
        self.callback_query.message.delete = AsyncMock()

class MockContext:
    def __init__(self, user_data=None):
        self.user_data = user_data or {
            'creating_task': True,
            'task_text': 'Тестовая задача',
            'department': 'assistants'
        }
        self.application = Mock()
        self.bot = Mock()

# Тест 1: new_task_start
@pytest.mark.asyncio
async def test_new_task_start_single_department():
    """Тест создания задачи для пользователя с одним отделом"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [('assistants', 'Ассистенты')]
        
        result = await new_task_start(update, context)
        
        # Проверяем, что пользователю предложили ввести текст
        update.message.reply_text.assert_called()
        assert "Введите текст задачи" in update.message.reply_text.call_args[0][0]
        assert result == 1  # WAITING_FOR_TASK_TEXT

@pytest.mark.asyncio
async def test_new_task_start_multiple_departments():
    """Тест создания задачи для пользователя с несколькими отделами"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [
            ('assistants', 'Ассистенты'),
            ('carpenters', 'Плотники')
        ]
        
        result = await new_task_start(update, context)
        
        # Проверяем, что пользователю предложили выбрать отдел
        update.message.reply_text.assert_called()
        assert "В какой отдел поставить задачу?" in update.message.reply_text.call_args[0][0]
        assert result == 3  # WAITING_FOR_DEPARTMENT_MEMBER

@pytest.mark.asyncio
async def test_new_task_start_no_departments():
    """Тест создания задачи для пользователя без отделов"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = []
        
        result = await new_task_start(update, context)
        
        # Проверяем, что пользователю отказали
        update.message.reply_text.assert_called()
        assert "Вы не состоите ни в одном отделе" in update.message.reply_text.call_args[0][0]

# Тест 2: receive_task_text
@pytest.mark.asyncio
async def test_receive_task_text_cancel():
    """Тест отмены создания задачи"""
    update = MockUpdate(text="❌ Отмена")
    context = MockContext()
    
    result = await receive_task_text(update, context)
    
    # Проверяем, что процесс отменен
    assert result == -1  # ConversationHandler.END

@pytest.mark.asyncio
async def test_receive_task_text_normal():
    """Тест получения текста задачи"""
    update = MockUpdate(text="Новая задача")
    # Убираем photo из мока, чтобы тест прошел по текстовому пути
    update.message.photo = None
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        result = await receive_task_text(update, context)
        
        # Проверяем, что предложили выбрать сотрудника
        update.message.reply_text.assert_called()
        assert "Кому назначить задачу?" in update.message.reply_text.call_args[0][0]
        assert result == 2  # WAITING_FOR_ASSIGN_TYPE

# Тест 3: assign_type_callback
@pytest.mark.asyncio
async def test_assign_type_callback_assign_none():
    """Тест выбора 'Без назначения'"""
    update = MockUpdate()
    update.callback_query.data = "assign_none"
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.assign_department') as mock_assign:
        mock_assign.return_value = None
        
        result = await assign_type_callback(update, context)
        
        # Проверяем, что assign_department был вызван
        mock_assign.assert_called_once()

@pytest.mark.asyncio
async def test_assign_type_callback_cancel():
    """Тест отмены в assign_type_callback"""
    update = MockUpdate()
    update.callback_query.data = "cancel_task"
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.cancel_task_callback') as mock_cancel:
        mock_cancel.return_value = None
        
        result = await assign_type_callback(update, context)
        
        # Проверяем, что cancel_task_callback был вызван
        mock_cancel.assert_called_once()

# Тест 4: assign_department
@pytest.mark.asyncio
async def test_assign_department_success():
    """Тест успешного назначения задачи"""
    update = MockUpdate()
    update.callback_query.data = "assign_none"
    context = MockContext()
    
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
                
                result = await assign_department(update, context)
                
                # Проверяем, что задача создана
                mock_add.assert_called()
                task = mock_add.call_args[0][0]
                assert task['assistant_id'] is None
                assert task['assistant_name'] == "Без назначения"
                assert result == -1  # ConversationHandler.END

@pytest.mark.asyncio
async def test_assign_department_invalid_user():
    """Тест назначения несуществующему пользователю"""
    update = MockUpdate()
    update.callback_query.data = "assign_999999"
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {
                'name': 'Ассистенты',
                'chat_id': -100123456789,
                'members': {'123': 'Тест Пользователь'}
            }
        }
        
        result = await assign_department(update, context)
        
        # Проверяем, что пользователю показана ошибка
        update.callback_query.message.reply_text.assert_called()
        assert "не состоит в этом отделе" in update.callback_query.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END

# Тест 5: assign_assistant
@pytest.mark.asyncio
async def test_assign_assistant_success():
    """Тест успешного назначения ассистенту"""
    update = MockUpdate()
    update.callback_query.data = "assign_123"
    context = MockContext()
    
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
                
                result = await assign_assistant(update, context)
                
                # Проверяем, что задача создана
                mock_add.assert_called()
                task = mock_add.call_args[0][0]
                assert task['assistant_id'] == 123
                assert task['assistant_name'] == "Тест Пользователь"
                assert result == -1  # ConversationHandler.END

# Тест 6: cancel_task_callback
@pytest.mark.asyncio
async def test_cancel_task_callback():
    """Тест отмены создания задачи"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.main_menu_keyboard') as mock_keyboard:
        mock_keyboard.return_value = Mock()
        
        result = await cancel_task_callback(update, context)
        
        # Проверяем, что процесс отменен
        update.callback_query.message.reply_text.assert_called()
        assert "Создание задачи отменено" in update.callback_query.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END

# Тест 7: list_tasks
@pytest.mark.asyncio
async def test_list_tasks():
    """Тест просмотра списка задач"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.DEPARTMENTS = {
            'assistants': {'name': 'Ассистенты'},
            'carpenters': {'name': 'Плотники'}
        }
        
        result = await list_tasks(update, context)
        
        # Проверяем, что пользователю показан выбор отделов
        update.message.reply_text.assert_called()
        assert "Выберите отдел" in update.message.reply_text.call_args[0][0]

# Тест 8: view_personal_tasks
@pytest.mark.asyncio
async def test_view_personal_tasks():
    """Тест просмотра личных задач"""
    update = MockUpdate()
    context = MockContext()
    
    with patch('handlers_veretevo.tasks.get_tasks') as mock_get:
        mock_get.return_value = [
            {
                'id': 1,
                'text': 'Тестовая задача',
                'author_id': 123,
                'status': 'новая'
            }
        ]
        
        result = await view_personal_tasks(update, context)
        
        # Проверяем, что пользователю показаны задачи
        update.message.reply_text.assert_called()
        assert "Тестовая задача" in update.message.reply_text.call_args[0][0]

# Тест 9: Обработка ошибок
@pytest.mark.asyncio
async def test_error_handling_invalid_callback():
    """Тест обработки некорректных callback данных"""
    update = MockUpdate()
    update.callback_query.data = "invalid_callback_data"
    context = MockContext()
    
    # Проверяем, что функция не падает с ошибкой
    try:
        result = await assign_type_callback(update, context)
    except Exception as e:
        pytest.fail(f"assign_type_callback не должен падать с ошибкой: {e}")

# Тест 10: Проверка контекста
@pytest.mark.asyncio
async def test_context_data_handling():
    """Тест обработки данных контекста"""
    update = MockUpdate()
    context = MockContext(user_data=None)  # Пустой контекст
    
    with patch('handlers_veretevo.tasks.department_service') as mock_dept:
        mock_dept.get_user_departments.return_value = [('assistants', 'Ассистенты')]
        
        result = await new_task_start(update, context)
        
        # Проверяем, что контекст обработан корректно
        assert context.user_data is not None
        assert 'department' in context.user_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 