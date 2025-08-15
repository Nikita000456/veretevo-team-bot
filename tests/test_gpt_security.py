#!/usr/bin/env python3
"""
Тест GPT функционала для чата охраны
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers_veretevo.gpt_handlers import get_department_from_chat
from services_veretevo.gpt_service import gpt_service

def test_department_detection():
    """Тестирует определение отдела по ID чата"""
    print("🧪 Тестирование определения отдела по ID чата...")
    
    # Тестовые ID чатов
    test_cases = [
        (-1002766433811, "assistants", "Ассистенты"),
        (-1002874667453, "carpenters", "Плотники"),
        (-1002295933154, "security", "Охрана"),
        (-1002844492561, "finance", "Финансы"),
        (-1002634456712, "construction", "Стройка"),
        (-1002588088668, "management", "Руководители"),
        (-4883128031, "info", "Инфо"),
        (123456789, "", "Неизвестный чат")
    ]
    
    for chat_id, expected_department, description in test_cases:
        result = get_department_from_chat(chat_id)
        status = "✅" if result == expected_department else "❌"
        print(f"{status} {description} (ID: {chat_id}) -> '{result}' (ожидалось: '{expected_department}')")
    
    print()

def test_gpt_service():
    """Тестирует GPT сервис"""
    print("🧪 Тестирование GPT сервиса...")
    
    # Проверяем статистику
    stats = gpt_service.get_cache_stats()
    print(f"📊 Статистика базы знаний:")
    print(f"   - Всего ответов: {stats['total_answers']}")
    print(f"   - Размер файла: {stats['file_size']} байт")
    print(f"   - Последнее сохранение: {stats['last_save']}")
    print()

def test_similar_questions():
    """Тестирует поиск похожих вопросов"""
    print("🧪 Тестирование поиска похожих вопросов...")
    
    # Добавляем тестовый вопрос в базу знаний
    test_question = "Как проверить безопасность объекта?"
    test_answer = "Необходимо провести обход территории, проверить все входы и выходы, убедиться в исправности систем безопасности."
    
    # Сохраняем тестовый ответ
    success = gpt_service.save_answer_template(test_question, test_answer, "security")
    print(f"💾 Сохранение тестового ответа: {'✅' if success else '❌'}")
    
    # Ищем похожий вопрос
    similar = gpt_service.find_similar_question("Проверить безопасность")
    if similar:
        print(f"🔍 Найден похожий вопрос: '{similar['question']}'")
        print(f"   Ответ: {similar['answer'][:50]}...")
    else:
        print("🔍 Похожий вопрос не найден")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 === ТЕСТ GPT ФУНКЦИОНАЛА ДЛЯ ЧАТА ОХРАНЫ ===\n")
    
    # Тестируем определение отдела
    test_department_detection()
    
    # Тестируем GPT сервис
    test_gpt_service()
    
    # Тестируем поиск похожих вопросов
    test_similar_questions()
    
    print("✅ Тестирование завершено!")
    print("\n📋 Рекомендации:")
    print("1. Отправьте сообщение в чат охраны (-1002295933154)")
    print("2. Проверьте, что появляется кнопка '💡 GPT-ответ'")
    print("3. Нажмите кнопку и проверьте генерацию ответа")
    print("4. Проверьте сохранение ответа в базу знаний")

if __name__ == "__main__":
    main() 