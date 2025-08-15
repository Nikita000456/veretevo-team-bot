import pytest
from utils_veretevo.keyboards import get_task_action_keyboard
from config_veretevo.constants import GENERAL_DIRECTOR_ID
import asyncio
from utils_veretevo.media import send_task_action_comment

# Примитивные моки для имитации Telegram API и контекста
class MockBot:
    def __init__(self):
        self.edited_messages = []
        self.sent_messages = []
    async def edit_message_text(self, chat_id, message_id, text, reply_markup, parse_mode):
        self.edited_messages.append((chat_id, message_id, text, reply_markup))
    async def send_message(self, chat_id, text):
        self.sent_messages.append((chat_id, text))

class MockContext:
    def __init__(self):
        self.bot = MockBot()
        self.application = type('app', (), {'bot_data': {}})()

@pytest.mark.asyncio
async def test_task_buttons_algorithm_full(monkeypatch):
    # 1. Создание задачи
    task = {
        "id": 1,
        "text": "Тестовая задача",
        "status": "новая",
        "author_id": 100,
        "author_name": "Автор",
        "department": "carpenters",
        "assistant_id": None,
        "assistant_name": None
    }
    department_members = ["100", "200"]
    # 2. Проверка кнопок для группы (user_id=None)
    keyboard = get_task_action_keyboard(task, None)
    button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert "Взять в работу" in button_texts
    assert "✅ Завершить" in button_texts
    assert "❌ Отменить" in button_texts
    # 3. Взятие задачи в работу
    task["status"] = "в работе"
    task["assistant_id"] = 200
    task["assistant_name"] = "Исполнитель"
    # Кнопка "Взять в работу" должна исчезнуть
    keyboard2 = get_task_action_keyboard(task, None)
    button_texts2 = [btn.text for row in keyboard2.inline_keyboard for btn in row]
    assert "Взять в работу" not in button_texts2
    assert "✅ Завершить" in button_texts2
    assert "❌ Отменить" in button_texts2
    # 4. Завершение задачи
    task["status"] = "завершено"
    keyboard3 = get_task_action_keyboard(task, None)
    button_texts3 = [btn.text for row in keyboard3.inline_keyboard for btn in row]
    assert "✅ Завершено" in button_texts3  # Теперь показываем информативную кнопку
    
    # 5. Попытка повторного завершения (должно быть запрещено)
    # (эмулируется через логику task_action_callback, но здесь только UI)
    
    # 6. Проверка прав: отменить может только автор или директор
    task["status"] = "новая"
    keyboard4 = get_task_action_keyboard(task, 100, department_members)
    button_texts4 = [btn.text for row in keyboard4.inline_keyboard for btn in row]
    assert "❌ Отменить" in button_texts4
    keyboard5 = get_task_action_keyboard(task, 200, department_members)
    button_texts5 = [btn.text for row in keyboard5.inline_keyboard for btn in row]
    assert "❌ Отменить" not in button_texts5
    keyboard6 = get_task_action_keyboard(task, GENERAL_DIRECTOR_ID, department_members)
    button_texts6 = [btn.text for row in keyboard6.inline_keyboard for btn in row]
    assert "❌ Отменить" in button_texts6
    
    # 7. Проверка, что нельзя завершить задачу, если не ответственный и не директор
    task["status"] = "в работе"
    keyboard7 = get_task_action_keyboard(task, 100, department_members)
    button_texts7 = [btn.text for row in keyboard7.inline_keyboard for btn in row]
    assert "✅ Завершить" not in button_texts7
    
    # 8. Проверка, что ответственный может завершить
    keyboard8 = get_task_action_keyboard(task, 200, department_members)
    button_texts8 = [btn.text for row in keyboard8.inline_keyboard for btn in row]
    assert "✅ Завершить" in button_texts8
    
    # 9. Проверка, что директор может завершить
    keyboard9 = get_task_action_keyboard(task, GENERAL_DIRECTOR_ID, department_members)
    button_texts9 = [btn.text for row in keyboard9.inline_keyboard for btn in row]
    assert "✅ Завершить" in button_texts9
    
    # 10. Проверка, что показывается информативная кнопка при статусе 'отменено'
    task["status"] = "отменено"
    keyboard10 = get_task_action_keyboard(task, None)
    button_texts10 = [btn.text for row in keyboard10.inline_keyboard for btn in row]
    assert "❌ Отменено" in button_texts10  # Теперь показываем информативную кнопку

# Удаляю декоратор @pytest.mark.asyncio, так как функция не async
def test_send_task_action_comment(monkeypatch):
    # Мокаем context.bot.send_message
    sent = {}
    class MockBot:
        async def send_message(self, chat_id, text):
            sent['chat_id'] = chat_id
            sent['text'] = text
    class MockContext:
        def __init__(self):
            self.bot = MockBot()
    # Пример задачи
    task = {
        "id": 1,
        "text": "Тестовая задача",
        "department": "carpenters"
    }
    # Мокаем DEPARTMENTS
    from services_veretevo import department_service
    department_service.DEPARTMENTS["carpenters"] = {
        "name": "Плотники",
        "chat_id": -1001234567890,
        "members": {"200": "Исполнитель"}
    }
    # Проверяем уведомление о взятии в работу
    asyncio.run(send_task_action_comment(MockContext(), task, "take", 200))
    assert sent['chat_id'] == -1001234567890
    assert "взял(а) задачу" in sent['text']
    assert "Тестовая задача" in sent['text']
    # Проверяем уведомление о завершении
    asyncio.run(send_task_action_comment(MockContext(), task, "finish", 200))
    assert "завершил(а) задачу" in sent['text']
    # Проверяем уведомление об отмене
    asyncio.run(send_task_action_comment(MockContext(), task, "cancel", 200))
    assert "отменил(а) задачу" in sent['text'] 