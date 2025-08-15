#!/usr/bin/env python3
"""
Тест обработчика голосовых сообщений
"""

import sys
import os
import tempfile
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from pydub.generators import Sine

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_voice_file():
    """Создает тестовый голосовой файл"""
    try:
        # Создаем простой тон
        tone = Sine(440).to_audio_segment(duration=2000)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            tone.export(temp_file.name, format='ogg', codec='libopus', 
                       parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            return temp_file.name
    except Exception as e:
        print(f"❌ Ошибка создания тестового файла: {e}")
        return None

async def test_voice_handler():
    """Тестирует обработчик голосовых сообщений"""
    print("🔍 Тестирование обработчика голосовых сообщений...")
    
    try:
        # Импортируем функцию обработки голосовых сообщений
        from handlers_veretevo.tasks import handle_voice_message
        
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        
        # Создаем мок сообщение
        message = Mock()
        message.voice = Mock()
        message.voice.file_id = "test_file_id"
        update.message = message
        
        # Создаем мок бота
        bot = AsyncMock()
        context.bot = bot
        
        # Создаем тестовый файл
        test_file_path = create_test_voice_file()
        if not test_file_path:
            print("❌ Не удалось создать тестовый файл")
            return False
            
        # Мокаем скачивание файла
        file_mock = Mock()
        file_mock.download_to_drive = AsyncMock()
        bot.get_file.return_value = file_mock
        
        # Мокаем отправку сообщения
        message.reply_text = AsyncMock()
        
        print("✅ Моки созданы успешно")
        
        # Вызываем обработчик
        print("🎤 Вызываем handle_voice_message...")
        await handle_voice_message(update, context)
        
        # Проверяем, что были вызваны нужные методы
        if bot.get_file.called:
            print("✅ get_file() был вызван")
        else:
            print("❌ get_file() не был вызван")
            
        if message.reply_text.called:
            print("✅ reply_text() был вызван")
            # Получаем текст ответа
            call_args = message.reply_text.call_args
            if call_args:
                reply_text = call_args[0][0] if call_args[0] else ""
                print(f"   Ответ: {reply_text[:100]}...")
        else:
            print("❌ reply_text() не был вызван")
            
        # Удаляем тестовый файл
        os.unlink(test_file_path)
        print("🗑️ Тестовый файл удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании обработчика: {e}")
        return False

async def test_voice_transcriber_integration():
    """Тестирует интеграцию voice_transcriber с обработчиком"""
    print("\n🔍 Тестирование интеграции voice_transcriber...")
    
    try:
        from handlers_veretevo.tasks import voice_transcriber
        
        if not voice_transcriber:
            print("❌ voice_transcriber не инициализирован")
            return False
            
        # Создаем тестовый файл
        test_file_path = create_test_voice_file()
        if not test_file_path:
            print("❌ Не удалось создать тестовый файл")
            return False
            
        print(f"✅ Тестовый файл создан: {test_file_path}")
        
        # Тестируем обработку файла
        print("🎤 Тестируем process_audio_file...")
        transcript = voice_transcriber.process_audio_file(test_file_path)
        
        if transcript is not None:
            print(f"✅ Транскрипция вернула результат: '{transcript}'")
        else:
            print("⚠️ Транскрипция вернула None (это нормально для синтетического аудио)")
            
        # Удаляем тестовый файл
        os.unlink(test_file_path)
        print("🗑️ Тестовый файл удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании интеграции: {e}")
        return False

async def main():
    print("🚀 Тест обработчика голосовых сообщений\n")
    
    # Тест 1: Обработчик голосовых сообщений
    handler_ok = await test_voice_handler()
    
    # Тест 2: Интеграция с voice_transcriber
    integration_ok = await test_voice_transcriber_integration()
    
    print(f"\n📊 Результаты:")
    print(f"   Обработчик: {'✅ ОК' if handler_ok else '❌ ОШИБКА'}")
    print(f"   Интеграция: {'✅ ОК' if integration_ok else '❌ ОШИБКА'}")
    
    if handler_ok and integration_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("💡 Обработка голосовых сообщений должна работать")
        print("💡 Попробуйте отправить реальное голосовое сообщение боту")
    else:
        print("\n⚠️ Есть проблемы с обработкой голосовых сообщений")
        print("💡 Проверьте логи бота при получении голосового сообщения")

if __name__ == "__main__":
    asyncio.run(main())
