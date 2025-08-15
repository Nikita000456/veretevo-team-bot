#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы транскрипции Yandex SpeechKit
"""

import os
import sys
import tempfile
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

def create_test_audio():
    """Создает тестовый аудиофайл с простым тоном"""
    try:
        # Создаем простой синусоидальный тон
        sample_rate = 48000
        duration = 2000  # 2 секунды
        frequency = 440  # нота ля
        
        # Генерируем синусоидальный сигнал
        sine_wave = Sine(frequency).to_audio_segment(duration=duration)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            sine_wave.export(temp_file.name, format='wav')
            return temp_file.name
    except Exception as e:
        print(f"[ОШИБКА] Не удалось создать тестовый аудиофайл: {e}")
        return None

def test_transcription():
    """Тестирует работу транскрипции"""
    print("🔍 Тестирование транскрипции Yandex SpeechKit...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Проверяем подключение
        print("🔗 Проверяем подключение к API...")
        if transcriber.test_connection():
            print("✅ Подключение к API работает")
        else:
            print("❌ Проблема с подключением к API")
            return False
        
        # Создаем тестовый аудиофайл
        print("🎵 Создаем тестовый аудиофайл...")
        test_audio_path = create_test_audio()
        if not test_audio_path:
            print("❌ Не удалось создать тестовый аудиофайл")
            return False
        
        print(f"✅ Тестовый аудиофайл создан: {test_audio_path}")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = transcriber.process_audio_file(test_audio_path)
        
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
        if 'test_audio_path' in locals() and os.path.exists(test_audio_path):
            try:
                os.unlink(test_audio_path)
                print("🗑️ Тестовый файл удален")
            except Exception as e:
                print(f"⚠️ Не удалось удалить тестовый файл: {e}")

def test_voice_transcriber_initialization():
    """Тестирует инициализацию voice_transcriber в tasks.py"""
    print("\n🔍 Тестирование инициализации voice_transcriber...")
    
    try:
        # Импортируем модуль tasks
        from handlers_veretevo.tasks import voice_transcriber
        
        if voice_transcriber is not None:
            print("✅ voice_transcriber инициализирован успешно")
            print(f"   Тип: {type(voice_transcriber)}")
            return True
        else:
            print("❌ voice_transcriber равен None")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке voice_transcriber: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов транскрипции...\n")
    
    # Тест 1: Инициализация voice_transcriber
    test1_passed = test_voice_transcriber_initialization()
    
    # Тест 2: Работа транскрипции
    test2_passed = test_transcription()
    
    print("\n📊 Результаты тестов:")
    print(f"   Инициализация voice_transcriber: {'✅ ПРОЙДЕН' if test1_passed else '❌ ПРОВАЛЕН'}")
    print(f"   Работа транскрипции: {'✅ ПРОЙДЕН' if test2_passed else '❌ ПРОВАЛЕН'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Все тесты пройдены! Транскрипция работает корректно.")
    else:
        print("\n⚠️ Обнаружены проблемы с транскрипцией.") 