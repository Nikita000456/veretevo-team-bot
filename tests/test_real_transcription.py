#!/usr/bin/env python3
"""
Тест транскрипции с реальным аудиофайлом
"""

import os
import sys
import tempfile
from pydub import AudioSegment
from pydub.generators import Sine

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

def create_test_voice_file():
    """Создает тестовый голосовой файл с простым тоном"""
    try:
        # Создаем простой синусоидальный тон (имитация голоса)
        sample_rate = 48000
        duration = 3000  # 3 секунды
        
        # Создаем тон с частотой человеческого голоса
        sine_wave = Sine(220).to_audio_segment(duration=duration)
        
        # Конвертируем в формат, похожий на голосовое сообщение
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            # Экспортируем в OGG формат с параметрами голосового сообщения
            sine_wave.export(
                temp_file.name, 
                format='ogg', 
                codec='libopus',
                parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"]
            )
            return temp_file.name
    except Exception as e:
        print(f"[ОШИБКА] Не удалось создать тестовый голосовой файл: {e}")
        return None

def test_real_transcription():
    """Тестирует транскрипцию с реальным файлом"""
    print("🔍 Тестирование транскрипции с реальным файлом...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Создаем тестовый голосовой файл
        print("🎵 Создаем тестовый голосовой файл...")
        test_voice_path = create_test_voice_file()
        if not test_voice_path:
            print("❌ Не удалось создать тестовый голосовой файл")
            return False
        
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

def test_voice_transcriber_in_tasks():
    """Тестирует voice_transcriber в контексте tasks.py"""
    print("\n🔍 Тестирование voice_transcriber в tasks.py...")
    
    try:
        # Импортируем модуль tasks
        from handlers_veretevo.tasks import voice_transcriber
        
        if voice_transcriber is not None:
            print("✅ voice_transcriber инициализирован успешно")
            print(f"   Тип: {type(voice_transcriber)}")
            
            # Тестируем создание транскрайбера
            test_transcriber = YandexSpeechKitTranscriber()
            print("✅ Новый транскрайбер создан успешно")
            
            return True
        else:
            print("❌ voice_transcriber равен None")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке voice_transcriber: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов реальной транскрипции...\n")
    
    # Тест 1: Инициализация voice_transcriber
    test1_passed = test_voice_transcriber_in_tasks()
    
    # Тест 2: Работа транскрипции с реальным файлом
    test2_passed = test_real_transcription()
    
    print("\n📊 Результаты тестов:")
    print(f"   Инициализация voice_transcriber: {'✅ ПРОЙДЕН' if test1_passed else '❌ ПРОВАЛЕН'}")
    print(f"   Работа транскрипции с реальным файлом: {'✅ ПРОЙДЕН' if test2_passed else '❌ ПРОВАЛЕН'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Все тесты пройдены! Транскрипция работает корректно.")
    else:
        print("\n⚠️ Обнаружены проблемы с транскрипцией.")
        
    print("\n💡 Рекомендации:")
    print("   1. Проверьте, что API ключ Yandex SpeechKit действителен")
    print("   2. Убедитесь, что Folder ID указан правильно")
    print("   3. Проверьте баланс в Yandex Cloud")
    print("   4. Попробуйте отправить голосовое сообщение в чат бота") 