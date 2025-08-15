import pytest
import asyncio

def test_basic_import():
    """Простой тест для проверки импортов"""
    assert True

def test_project_structure():
    """Тест структуры проекта"""
    import os
    assert os.path.exists('main.py')
    assert os.path.exists('requirements.txt')
    assert os.path.exists('handlers_veretevo')
    assert os.path.exists('services_veretevo')

@pytest.mark.asyncio
async def test_async_basic():
    """Простой асинхронный тест"""
    await asyncio.sleep(0.001)
    assert True 