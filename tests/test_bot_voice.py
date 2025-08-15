#!/usr/bin/env python3
"""
Тест работы бота с голосовыми сообщениями
"""

import os
import sys
import asyncio
import tempfile
from pydub import AudioSegment
from pydub.generators import Sine

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_veretevo.env import TELEGRAM_TOKEN, ASSISTANTS_CHAT_ID
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

async def test_voice_transcription():
    """Тестирует транскрипцию голосового сообщения"""
    print("🔍 Тестирование транскрипции голосового сообщения...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Создаем тестовый голосовой файл
        print("🎵 Создаем тестовый голосовой файл...")
        
        # Создаем более сложный аудиофайл (имитация речи)
        sample_rate = 48000
        duration = 2000  # 2 секунды
        
        # Создаем несколько тонов разной частоты (имитация речи)
        audio = AudioSegment.silent(duration=duration)
        
        # Добавляем несколько тонов разной частоты
        frequencies = [220, 440, 330, 550]  # Разные частоты
        segment_duration = duration // len(frequencies)
        
        for i, freq in enumerate(frequencies):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            tone = Sine(freq).to_audio_segment(duration=segment_duration)
            audio = audio.overlay(tone, position=start_time)
        
        # Конвертируем в OGG формат
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            audio.export(
                temp_file.name, 
                format='ogg', 
                codec='libopus',
                parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"]
            )
            test_voice_path = temp_file.name
        
        print(f"✅ Тестовый голосовой файл создан: {test_voice_path}")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = transcriber.process_audio_file(test_voice_path)
        
        if transcript:
            print(f"✅ Транскрипция работает! Результат: '{transcript}'")
            return True
        else:
            print("❌ Транскрипция не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        # Удаляем тестовый файл
        if 'test_voice_path' in locals() and os.path.exists(test_voice_path):
            try:
                os.unlink(test_voice_path)
                print("🗑️ Тестовый файл удален")
            except Exception as e:
                print(f"⚠️ Не удалось удалить тестовый файл: {e}")

async def test_bot_connection():
    """Тестирует подключение к боту"""
    print("\n🔍 Тестирование подключения к боту...")
    
    try:
        from telegram import Bot
        
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        print(f"   Имя: {bot_info.first_name}")
        
        # Проверяем доступ к чату ассистентов
        try:
            chat = await bot.get_chat(ASSISTANTS_CHAT_ID)
            print(f"✅ Доступ к чату ассистентов: {chat.title}")
            print(f"   Тип чата: {chat.type}")
            return True
        except Exception as e:
            print(f"❌ Нет доступа к чату ассистентов: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к боту: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов бота...\n")
    
    # Тест 1: Подключение к боту
    test1_passed = await test_bot_connection()
    
    # Тест 2: Транскрипция голосового сообщения
    test2_passed = await test_voice_transcription()
    
    print("\n📊 Результаты тестов:")
    print(f"   Подключение к боту: {'✅ ПРОЙДЕН' if test1_passed else '❌ ПРОВАЛЕН'}")
    print(f"   Транскрипция голосового сообщения: {'✅ ПРОЙДЕН' if test2_passed else '❌ ПРОВАЛЕН'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Все тесты пройдены! Бот работает корректно.")
    else:
        print("\n⚠️ Обнаружены проблемы с ботом.")
        
    print("\n💡 Рекомендации:")
    print("   1. Отправьте голосовое сообщение в чат ассистентов")
    print("   2. Проверьте логи бота: tail -f logs/bot.log")
    print("   3. Убедитесь, что бот имеет права на чтение сообщений в чате")

if __name__ == "__main__":
    asyncio.run(main()) 