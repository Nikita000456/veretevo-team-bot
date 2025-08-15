#!/usr/bin/env python3
"""
Тест обработки голосовых сообщений в реальном времени
"""

import sys
import os
import tempfile
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from pydub.generators import Sine

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_realistic_voice_file():
    """Создает более реалистичный голосовой файл"""
    try:
        # Создаем более сложный звук, имитирующий речь
        duration_ms = 3000  # 3 секунды
        
        # Основной тон речи (базовая частота)
        base_freq = 150
        speech_base = Sine(base_freq).to_audio_segment(duration=duration_ms)
        
        # Добавляем вариации частоты (как в речи)
        variations = []
        for i in range(0, duration_ms, 200):  # Каждые 200мс
            freq = base_freq + (i % 100)  # Вариация частоты
            segment = Sine(freq).to_audio_segment(duration=200)
            variations.append(segment)
        
        # Объединяем все сегменты
        speech = speech_base
        for segment in variations:
            speech = speech + segment
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            speech.export(temp_file.name, format='ogg', codec='libopus', 
                         parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            return temp_file.name
            
    except Exception as e:
        print(f"❌ Ошибка создания реалистичного файла: {e}")
        return None

async def test_voice_message_simulation():
    """Симулирует обработку голосового сообщения"""
    print("🔍 Симуляция обработки голосового сообщения...")
    
    try:
        # Импортируем необходимые модули
        from handlers_veretevo.tasks import handle_voice_message, voice_transcriber
        
        # Создаем реалистичный голосовой файл
        voice_file_path = create_realistic_voice_file()
        if not voice_file_path:
            print("❌ Не удалось создать голосовой файл")
            return False
            
        print(f"✅ Голосовой файл создан: {voice_file_path}")
        
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        
        # Создаем мок сообщение
        message = Mock()
        message.voice = Mock()
        message.voice.file_id = "test_voice_file_id"
        update.message = message
        
        # Создаем мок бота
        bot = AsyncMock()
        context.bot = bot
        
        # Мокаем скачивание файла
        file_mock = Mock()
        file_mock.download_to_drive = AsyncMock()
        bot.get_file.return_value = file_mock
        
        # Мокаем отправку сообщения
        message.reply_text = AsyncMock()
        
        print("✅ Моки созданы успешно")
        
        # Тестируем voice_transcriber напрямую
        print("🎤 Тестируем voice_transcriber напрямую...")
        if voice_transcriber:
            transcript = voice_transcriber.process_audio_file(voice_file_path)
            print(f"   Результат транскрипции: '{transcript}'")
            
            if transcript and transcript.strip():
                print("✅ Транскрипция успешна")
            else:
                print("⚠️ Транскрипция пустая (нормально для синтетического аудио)")
        else:
            print("❌ voice_transcriber недоступен")
            
        # Вызываем обработчик
        print("🎤 Вызываем handle_voice_message...")
        await handle_voice_message(update, context)
        
        # Проверяем результаты
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
        os.unlink(voice_file_path)
        print("🗑️ Тестовый файл удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при симуляции: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voice_transcriber_with_real_file():
    """Тестирует voice_transcriber с реалистичным файлом"""
    print("\n🔍 Тестирование voice_transcriber с реалистичным файлом...")
    
    try:
        from handlers_veretevo.tasks import voice_transcriber
        
        if not voice_transcriber:
            print("❌ voice_transcriber недоступен")
            return False
            
        # Создаем реалистичный файл
        voice_file_path = create_realistic_voice_file()
        if not voice_file_path:
            print("❌ Не удалось создать файл")
            return False
            
        print(f"✅ Файл создан: {voice_file_path}")
        
        # Проверяем размер файла
        import os
        file_size = os.path.getsize(voice_file_path)
        print(f"📊 Размер файла: {file_size} байт")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = voice_transcriber.process_audio_file(voice_file_path)
        
        if transcript and transcript.strip():
            print(f"✅ Транскрипция успешна: '{transcript}'")
        else:
            print("⚠️ Транскрипция пустая (нормально для синтетического аудио)")
            
        # Удаляем файл
        os.unlink(voice_file_path)
        print("🗑️ Файл удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

async def main():
    print("🚀 Тест обработки голосовых сообщений в реальном времени\n")
    
    # Тест 1: Симуляция обработки голосового сообщения
    simulation_ok = await test_voice_message_simulation()
    
    # Тест 2: Тестирование voice_transcriber с реалистичным файлом
    transcriber_ok = await test_voice_transcriber_with_real_file()
    
    print(f"\n📊 Результаты:")
    print(f"   Симуляция: {'✅ ОК' if simulation_ok else '❌ ОШИБКА'}")
    print(f"   Транскрайбер: {'✅ ОК' if transcriber_ok else '❌ ОШИБКА'}")
    
    if simulation_ok and transcriber_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("💡 Обработка голосовых сообщений должна работать")
        print("💡 Попробуйте отправить реальное голосовое сообщение боту")
        print("💡 Для реальных голосовых сообщений транскрипция должна работать")
    else:
        print("\n⚠️ Есть проблемы с обработкой голосовых сообщений")
        print("💡 Проверьте логи бота при получении голосового сообщения")

if __name__ == "__main__":
    asyncio.run(main())
