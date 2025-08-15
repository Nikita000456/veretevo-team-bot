#!/usr/bin/env python3
"""
Тест транскрипции с более реалистичным голосовым сообщением
"""

import os
import tempfile
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

def create_realistic_voice():
    """Создает более реалистичный голосовой файл с речью"""
    try:
        # Создаем базовый тон речи (200-300 Hz)
        sample_rate = 48000
        duration_ms = 3000  # 3 секунды
        
        # Создаем основной тон речи
        base_freq = 220  # Базовая частота речи
        base_tone = Sine(base_freq).to_audio_segment(duration=duration_ms)
        
        # Добавляем гармоники для более реалистичного звука
        harmonics = []
        for i in range(2, 5):  # Добавляем 2-4 гармоники
            harmonic = Sine(base_freq * i).to_audio_segment(duration=duration_ms)
            harmonic = harmonic - 20  # Уменьшаем громкость гармоник
            harmonics.append(harmonic)
        
        # Создаем шум для реалистичности
        noise = WhiteNoise().to_audio_segment(duration=duration_ms)
        noise = noise - 30  # Очень тихий шум
        
        # Смешиваем все компоненты
        voice = base_tone
        for harmonic in harmonics:
            voice = voice.overlay(harmonic)
        voice = voice.overlay(noise)
        
        # Нормализуем громкость
        voice = voice.normalize()
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            voice.export(temp_file.name, format='ogg', codec='libopus', 
                        parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            return temp_file.name
            
    except Exception as e:
        print(f"[ОШИБКА] Не удалось создать голосовой файл: {e}")
        return None

def test_realistic_transcription():
    """Тестирует транскрипцию с реалистичным голосом"""
    print("🔍 Тестирование транскрипции с реалистичным голосом...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Тестируем подключение
        print("🔗 Проверяем подключение к API...")
        if transcriber.test_connection():
            print("✅ Подключение к API работает")
        else:
            print("❌ Проблемы с подключением к API")
            return False
        
        # Создаем реалистичный голосовой файл
        print("🎵 Создаем реалистичный голосовой файл...")
        voice_path = create_realistic_voice()
        if not voice_path:
            print("❌ Не удалось создать голосовой файл")
            return False
        
        print(f"✅ Голосовой файл создан: {voice_path}")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = transcriber.process_audio_file(voice_path)
        
        if transcript and transcript.strip():
            print(f"✅ Транскрипция успешна: '{transcript}'")
            return True
        else:
            print("❌ Транскрипция вернула пустой результат")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        # Удаляем временный файл
        if 'voice_path' in locals() and os.path.exists(voice_path):
            os.unlink(voice_path)
            print("🗑️ Временный файл удален")

def main():
    print("🚀 Тест транскрипции с реалистичным голосом\n")
    
    # Запускаем тест
    success = test_realistic_transcription()
    
    print(f"\n📊 Результат теста: {'✅ УСПЕХ' if success else '❌ ПРОВАЛ'}")
    
    if not success:
        print("\n⚠️ Возможные причины проблемы:")
        print("   1. API ключ Yandex SpeechKit недействителен")
        print("   2. Недостаточно средств на балансе Yandex Cloud")
        print("   3. Проблемы с настройками API")
        print("   4. Тестовый файл слишком короткий или тихий")

if __name__ == "__main__":
    main()
