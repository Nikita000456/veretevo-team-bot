#!/usr/bin/env python3
"""
Финальный тест транскрипции после перезапуска бота
"""

import os
import tempfile
from pydub import AudioSegment
from pydub.generators import Sine
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

def test_transcription_after_restart():
    """Тестирует транскрипцию после перезапуска бота"""
    print("🔍 Тестирование транскрипции после перезапуска бота...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Проверяем учетные данные
        print(f"🔑 API Key: {transcriber.api_key[:10]}...")
        print(f"📁 Folder ID: {transcriber.folder_id}")
        
        # Тестируем подключение
        print("🔗 Проверяем подключение к API...")
        if transcriber.test_connection():
            print("✅ Подключение к API работает")
        else:
            print("❌ Проблемы с подключением к API")
            return False
        
        # Создаем тестовый аудиофайл
        print("🎵 Создаем тестовый аудиофайл...")
        tone = Sine(440).to_audio_segment(duration=2000)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            tone.export(temp_file.name, format='ogg', codec='libopus', 
                       parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            audio_path = temp_file.name
        
        print(f"✅ Аудиофайл создан: {audio_path}")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = transcriber.process_audio_file(audio_path)
        
        if transcript and transcript.strip():
            print(f"✅ Транскрипция успешна: '{transcript}'")
            return True
        else:
            print("❌ Транскрипция вернула пустой результат")
            print("💡 Это нормально для синтетического тона")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        # Удаляем временный файл
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.unlink(audio_path)
            print("🗑️ Временный файл удален")

def check_bot_status():
    """Проверяет статус бота"""
    print("\n🔍 Проверка статуса бота...")
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'python' in proc.info['name'] and 'main.py' in ' '.join(proc.info['cmdline'] or []):
                print(f"✅ Бот запущен (PID: {proc.info['pid']})")
                return True
        print("❌ Бот не найден в процессах")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса: {e}")
        return False

def main():
    print("🚀 Финальный тест транскрипции\n")
    
    # Проверяем статус бота
    bot_running = check_bot_status()
    
    # Тестируем транскрипцию
    transcription_works = test_transcription_after_restart()
    
    print(f"\n📊 Результаты:")
    print(f"   Бот запущен: {'✅ ДА' if bot_running else '❌ НЕТ'}")
    print(f"   API работает: {'✅ ДА' if transcription_works else '❌ НЕТ'}")
    
    if bot_running and transcription_works:
        print("\n🎉 Транскрипция должна работать!")
        print("💡 Попробуйте отправить реальное голосовое сообщение боту")
    else:
        print("\n⚠️ Есть проблемы:")
        if not bot_running:
            print("   - Бот не запущен")
        if not transcription_works:
            print("   - API не работает")

if __name__ == "__main__":
    main()
