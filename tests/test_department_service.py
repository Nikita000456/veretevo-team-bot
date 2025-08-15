import pytest
import json
from services_veretevo import department_service

def test_get_user_departments(tmp_path, monkeypatch):
    # Подготовка: временный файл отделов
    test_file = tmp_path / "departments_config.json"
    departments = {
        "assistants": {
            "name": "Ассистенты",
            "members": {"123": "Иван"}
        },
        "finance": {
            "name": "Финансы",
            "members": {"456": "Петр"}
        }
    }
    test_file.write_text(json.dumps(departments, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(department_service, "DEPARTMENTS_JSON_PATH", str(test_file))
    department_service.load_departments()
    # Проверяем, что пользователь найден в отделе
    deps = department_service.get_user_departments(123)
    assert deps == [("assistants", "Ассистенты")]
    deps2 = department_service.get_user_departments(456)
    assert deps2 == [("finance", "Финансы")]
    deps3 = department_service.get_user_departments(789)
    assert deps3 == [] 