import pytest
from services_veretevo import task_service

def test_add_and_get_task(monkeypatch):
    # Очищаем задачи
    monkeypatch.setattr(task_service, "tasks", [])
    # Добавляем задачу
    task = {
        "id": 1,
        "text": "Тестовая задача",
        "status": "новая",
        "author_id": 123,
        "author_name": "Тест Автор"
    }
    task_service.add_or_update_task(task)
    # Проверяем, что задача добавлена
    loaded = task_service.get_task_by_id(1)
    assert loaded is not None
    assert loaded["text"] == "Тестовая задача"
    # Проверяем, что задача сохраняется в файл
    task_service.save_tasks()
    monkeypatch.setattr(task_service, "tasks", [])
    task_service.load_tasks()
    loaded2 = task_service.get_task_by_id(1)
    assert loaded2 is not None
    assert loaded2["author_name"] == "Тест Автор" 

def test_task_lifecycle_for_departments(monkeypatch):
    monkeypatch.setattr(task_service, "tasks", [])
    # Создание задачи для отдела 'carpenters'
    task1 = {
        "id": 101,
        "text": "Задача для плотников",
        "status": "новая",
        "author_id": 1,
        "author_name": "Автор 1",
        "department": "carpenters"
    }
    task_service.add_or_update_task(task1)
    loaded1 = task_service.get_task_by_id(101)
    assert loaded1["department"] == "carpenters"
    assert loaded1["status"] == "новая"
    # Завершение задачи
    loaded1["status"] = "завершено"
    task_service.add_or_update_task(loaded1)
    loaded1_done = task_service.get_task_by_id(101)
    assert loaded1_done["status"] == "завершено"
    # Создание задачи для отдела 'security'
    task2 = {
        "id": 102,
        "text": "Задача для охраны",
        "status": "новая",
        "author_id": 2,
        "author_name": "Автор 2",
        "department": "security"
    }
    task_service.add_or_update_task(task2)
    loaded2 = task_service.get_task_by_id(102)
    assert loaded2["department"] == "security"
    assert loaded2["status"] == "новая"
    # Отмена задачи
    loaded2["status"] = "отменено"
    task_service.add_or_update_task(loaded2)
    loaded2_cancel = task_service.get_task_by_id(102)
    assert loaded2_cancel["status"] == "отменено" 