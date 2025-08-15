#!/usr/bin/env python3
"""
Тест новой логики GPT подсказок
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers_veretevo.gpt_handlers import get_department_from_chat
from config_veretevo.constants import GENERAL_DIRECTOR_ID

def test_new_gpt_logic():
    """Тестирует новую логику GPT подсказок"""
    print("🧪 Тестирование новой логики GPT подсказок...")
    
    print("\n📋 Новая логика:")
    print("✅ GPT подсказки появляются, когда ДРУГИЕ люди пишут сообщения")
    print("✅ Подсказки отправляются директору в ЛИЧНЫЙ чат")
    print("✅ Директор может ответить из личного чата в групповой чат")
    print("❌ GPT подсказки НЕ появляются для сообщений директора")
    
    print(f"\n👤 Директор ID: {GENERAL_DIRECTOR_ID}")
    print("📱 Подсказки будут приходить в личный чат директора")
    
    print("\n🎯 Как это работает:")
    print("1. Кто-то пишет сообщение в чат охраны")
    print("2. Бот отправляет GPT-подсказку директору в личный чат")
    print("3. Директор нажимает '💡 GPT-ответ' в личном чате")
    print("4. Ответ отправляется в групповой чат от имени директора")
    
    print("\n📋 Поддерживаемые чаты:")
    print(f"   - Ассистенты (-1002766433811) -> {get_department_from_chat(-1002766433811)}")
    print(f"   - Плотники (-1002874667453) -> {get_department_from_chat(-1002874667453)}")
    print(f"   - Охрана (-1002295933154) -> {get_department_from_chat(-1002295933154)}")
    print(f"   - Финансы (-1002844492561) -> {get_department_from_chat(-1002844492561)}")
    print(f"   - Стройка (-1002634456712) -> {get_department_from_chat(-1002634456712)}")
    print(f"   - Руководители (-1002588088668) -> {get_department_from_chat(-1002588088668)}")
    print(f"   - Инфо (-4883128031) -> {get_department_from_chat(-4883128031)}")
    
    print("\n✅ Тестирование завершено!")
    print("\n📋 Для тестирования:")
    print("1. Попросите кого-то написать сообщение в чат охраны")
    print("2. Проверьте, что директор получил подсказку в личный чат")
    print("3. Нажмите '💡 GPT-ответ' и проверьте ответ в групповом чате")

if __name__ == "__main__":
    test_new_gpt_logic() 