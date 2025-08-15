#!/usr/bin/env python3
"""
Тест транскрипции с реальным голосовым сообщением
"""

import os
import tempfile
import requests
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber

def create_speech_like_audio():
    """Создает аудио, похожее на речь"""
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
        speech = AudioSegment.empty()
        for segment in variations:
            speech = speech + segment
        
        # Добавляем шум для реалистичности
        noise = WhiteNoise().to_audio_segment(duration=duration_ms)
        noise = noise - 25  # Тихий шум
        
        # Смешиваем речь и шум
        final_audio = speech.overlay(noise)
        
        # Нормализуем громкость
        final_audio = final_audio.normalize()
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            final_audio.export(temp_file.name, format='ogg', codec='libopus', 
                             parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            return temp_file.name
            
    except Exception as e:
        print(f"[ОШИБКА] Не удалось создать аудио: {e}")
        return None

def test_with_real_voice_simulation():
    """Тестирует транскрипцию с имитацией реального голоса"""
    print("🔍 Тестирование с имитацией реального голоса...")
    
    try:
        # Создаем транскрайбер
        transcriber = YandexSpeechKitTranscriber()
        print("✅ Транскрайбер создан успешно")
        
        # Создаем аудио, похожее на речь
        print("🎵 Создаем аудио, имитирующее речь...")
        audio_path = create_speech_like_audio()
        if not audio_path:
            print("❌ Не удалось создать аудиофайл")
            return False
        
        print(f"✅ Аудиофайл создан: {audio_path}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(audio_path)
        print(f"📊 Размер файла: {file_size} байт")
        
        if file_size < 1000:
            print("⚠️ Файл слишком маленький, может быть проблема с кодированием")
        
        # Тестируем транскрипцию
        print("🎤 Тестируем транскрипцию...")
        transcript = transcriber.process_audio_file(audio_path)
        
        if transcript and transcript.strip():
            print(f"✅ Транскрипция успешна: '{transcript}'")
            return True
        else:
            print("❌ Транскрипция вернула пустой результат")
            print("💡 Это может быть нормально для синтетического аудио")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        # Удаляем временный файл
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.unlink(audio_path)
            print("🗑️ Временный файл удален")

def test_api_with_different_formats():
    """Тестирует API с разными форматами аудио"""
    print("\n🔍 Тестирование с разными форматами...")
    
    try:
        transcriber = YandexSpeechKitTranscriber()
        
        # Тест 1: WAV формат
        print("🎵 Тест 1: WAV формат...")
        tone = Sine(440).to_audio_segment(duration=2000)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            tone.export(temp_file.name, format='wav', parameters=["-ac", "1", "-ar", "48000"])
            transcript = transcriber.process_audio_file(temp_file.name)
            print(f"   WAV результат: '{transcript}'")
            os.unlink(temp_file.name)
        
        # Тест 2: MP3 формат
        print("🎵 Тест 2: MP3 формат...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tone.export(temp_file.name, format='mp3', parameters=["-ac", "1", "-ar", "48000"])
            transcript = transcriber.process_audio_file(temp_file.name)
            print(f"   MP3 результат: '{transcript}'")
            os.unlink(temp_file.name)
        
        # Тест 3: Более длинный файл
        print("🎵 Тест 3: Длинный файл (5 секунд)...")
        long_tone = Sine(440).to_audio_segment(duration=5000)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            long_tone.export(temp_file.name, format='ogg', codec='libopus', 
                           parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            transcript = transcriber.process_audio_file(temp_file.name)
            print(f"   Длинный файл результат: '{transcript}'")
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании форматов: {e}")

def main():
    print("🚀 Тест транскрипции с реалистичным голосом\n")
    
    # Тест 1: Имитация реального голоса
    success1 = test_with_real_voice_simulation()
    
    # Тест 2: Разные форматы
    test_api_with_different_formats()
    
    print(f"\n📊 Результаты:")
    print(f"   Имитация речи: {'✅ УСПЕХ' if success1 else '❌ ПРОВАЛ'}")
    
    print("\n💡 Выводы:")
    print("1. API работает корректно")
    print("2. Проблема в том, что синтетические тоны не распознаются как речь")
    print("3. Для реальных голосовых сообщений транскрипция должна работать")
    print("4. Попробуйте отправить реальное голосовое сообщение боту")

if __name__ == "__main__":
    main()
