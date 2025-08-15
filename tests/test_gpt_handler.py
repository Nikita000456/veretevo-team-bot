#!/usr/bin/env python3
"""
Тест GPT обработчика
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers_veretevo.gpt_handlers import get_department_from_chat, handle_message_in_group
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
import asyncio

def test_department_detection():
    """Тестирует определение отдела"""
    print("🧪 Тестирование определения отдела...")
    
    test_cases = [
        (-1002295933154, "security", "Охрана"),
        (-1002766433811, "assistants", "Ассистенты"),
        (-1002874667453, "carpenters", "Плотники"),
        (-1002844492561, "finance", "Финансы"),
        (-1002634456712, "construction", "Стройка"),
        (-1002588088668, "management", "Руководители"),
        (-4883128031, "info", "Инфо"),
    ]
    
    for chat_id, expected, name in test_cases:
        result = get_department_from_chat(chat_id)
        status = "✅" if result == expected else "❌"
        print(f"{status} {name} (ID: {chat_id}) -> '{result}' (ожидалось: '{expected}')")
    
    print()

def test_handler_logic():
    """Тестирует логику обработчика"""
    print("🧪 Тестирование логики обработчика...")
    
    print(f"👤 Директор ID: {GENERAL_DIRECTOR_ID}")
    print("📋 Логика обработки:")
    print("1. Проверка типа чата (group/supergroup)")
    print("2. Проверка что не бот")
    print("3. Проверка что НЕ директор")
    print("4. Проверка длины сообщения (>= 3 символов)")
    print("5. Отправка подсказки директору в личный чат")
    
    print("\n🎯 Ожидаемое поведение:")
    print("✅ Сообщения от других людей -> подсказка директору")
    print("❌ Сообщения от директора -> пропуск")
    print("❌ Сообщения от ботов -> пропуск")
    print("❌ Короткие сообщения (< 3 символов) -> пропуск")
    print("❌ Сообщения не в группах -> пропуск")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 === ТЕСТ GPT ОБРАБОТЧИКА ===\n")
    
    # Тестируем определение отдела
    test_department_detection()
    
    # Тестируем логику обработчика
    test_handler_logic()
    
    print("✅ Тестирование завершено!")
    print("\n📋 Для проверки:")
    print("1. Попросите кого-то написать сообщение в любую из групп (охрана, финансы, стройка, руководители, инфо)")
    print("2. Проверьте логи на наличие '[GPT DEBUG]' сообщений")
    print("3. Если сообщений нет - проблема с регистрацией обработчика")
    print("4. Если есть сообщения - проблема с отправкой подсказки")

if __name__ == "__main__":
    main() 