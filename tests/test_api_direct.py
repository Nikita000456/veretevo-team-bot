#!/usr/bin/env python3
"""
Прямой тест API Yandex SpeechKit для диагностики проблем
"""

import requests
import tempfile
import os
from pydub import AudioSegment
from pydub.generators import Sine
from config_veretevo.env import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID

def test_api_directly():
    """Прямой тест API без использования класса транскрайбера"""
    print("🔍 Прямой тест API Yandex SpeechKit...")
    
    try:
        # Создаем простой аудиофайл
        print("🎵 Создаем тестовый аудиофайл...")
        duration_ms = 2000  # 2 секунды
        tone = Sine(440).to_audio_segment(duration=duration_ms)  # Ля первой октавы
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            tone.export(temp_file.name, format='ogg', codec='libopus', 
                       parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            audio_path = temp_file.name
        
        print(f"✅ Аудиофайл создан: {audio_path}")
        
        # Читаем аудиофайл
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        print(f"📊 Размер аудио данных: {len(audio_data)} байт")
        
        # Формируем запрос к API
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        params = {
            'folderId': YANDEX_FOLDER_ID,
            'lang': 'ru-RU',
            'model': 'general:rc',
            'sampleRateHertz': '48000',
            'profanityFilter': 'false',
            'partialResults': 'false'
        }
        headers = {
            'Authorization': f'Api-Key {YANDEX_SPEECHKIT_API_KEY}',
            'Content-Type': 'application/octet-stream'
        }
        
        print(f"🌐 URL: {url}")
        print(f"📋 Параметры: {params}")
        print(f"🔑 API Key: {YANDEX_SPEECHKIT_API_KEY[:10]}...")
        print(f"📁 Folder ID: {YANDEX_FOLDER_ID}")
        
        # Отправляем запрос
        print("📤 Отправляем запрос к API...")
        response = requests.post(url, params=params, headers=headers, data=audio_data, timeout=30)
        
        print(f"📥 Получен ответ: статус {response.status_code}")
        print(f"📄 Заголовки ответа: {dict(response.headers)}")
        print(f"📝 Тело ответа: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ JSON ответ: {result}")
                if 'result' in result:
                    transcript = result['result']
                    if transcript:
                        print(f"🎤 Транскрипция: '{transcript}'")
                    else:
                        print("⚠️ Транскрипция пустая")
                else:
                    print("❌ Нет поля 'result' в ответе")
            except Exception as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        # Удаляем временный файл
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.unlink(audio_path)
            print("🗑️ Временный файл удален")

def test_api_balance():
    """Проверяет баланс и доступность API"""
    print("\n💰 Проверка баланса API...")
    
    try:
        # Проверяем доступность API через простой запрос
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        params = {
            'folderId': YANDEX_FOLDER_ID,
            'lang': 'ru-RU',
            'model': 'general:rc',
            'sampleRateHertz': '48000'
        }
        headers = {
            'Authorization': f'Api-Key {YANDEX_SPEECHKIT_API_KEY}',
            'Content-Type': 'application/octet-stream'
        }
        
        # Отправляем минимальный запрос (1 байт)
        response = requests.post(url, params=params, headers=headers, data=b'\x00', timeout=10)
        
        print(f"📊 Статус проверки баланса: {response.status_code}")
        print(f"📄 Ответ: {response.text}")
        
        if response.status_code == 400:
            print("✅ API доступен, но запрос некорректный (ожидаемо)")
        elif response.status_code == 401:
            print("❌ Ошибка авторизации - проверьте API ключ")
        elif response.status_code == 403:
            print("❌ Доступ запрещен - проверьте права доступа")
        elif response.status_code == 429:
            print("❌ Превышен лимит запросов")
        else:
            print(f"ℹ️ Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке баланса: {e}")

def main():
    print("🚀 Диагностика API Yandex SpeechKit\n")
    
    # Тест 1: Прямой запрос к API
    test_api_directly()
    
    # Тест 2: Проверка баланса
    test_api_balance()
    
    print("\n📋 Рекомендации:")
    print("1. Проверьте баланс в Yandex Cloud Console")
    print("2. Убедитесь, что API ключ действителен")
    print("3. Проверьте права доступа к SpeechKit")
    print("4. Попробуйте создать новый API ключ")

if __name__ == "__main__":
    main()
