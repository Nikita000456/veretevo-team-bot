#!/usr/bin/env python3
"""
Тест разных API ключей и folder ID
"""

import requests
import tempfile
import os
from pydub import AudioSegment
from pydub.generators import Sine
from config_veretevo.env import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID

def test_api_with_different_credentials():
    """Тестирует API с разными учетными данными"""
    print("🔍 Тестирование API с разными учетными данными...")
    
    # Получаем текущие учетные данные
    current_api_key = YANDEX_SPEECHKIT_API_KEY
    current_folder_id = YANDEX_FOLDER_ID
    
    print(f"🔑 Текущий API Key: {current_api_key[:10]}...")
    print(f"📁 Текущий Folder ID: {current_folder_id}")
    
    # Создаем простой аудиофайл
    tone = Sine(440).to_audio_segment(duration=2000)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
        tone.export(temp_file.name, format='ogg', codec='libopus', 
                   parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
        audio_path = temp_file.name
    
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Тест 1: Текущие учетные данные
        print("\n📋 Тест 1: Текущие учетные данные...")
        url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        params = {
            'folderId': current_folder_id,
            'lang': 'ru-RU',
            'model': 'general:rc',
            'sampleRateHertz': '48000',
            'profanityFilter': 'false',
            'partialResults': 'false'
        }
        headers = {
            'Authorization': f'Api-Key {current_api_key}',
            'Content-Type': 'application/octet-stream'
        }
        
        response = requests.post(url, params=params, headers=headers, data=audio_data, timeout=30)
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
        # Тест 2: Проверка авторизации с минимальным запросом
        print(f"\n📋 Тест 2: Проверка авторизации...")
        response = requests.post(url, params=params, headers=headers, data=b'\x00', timeout=10)
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        # Удаляем временный файл
        if os.path.exists(audio_path):
            os.unlink(audio_path)

def check_environment_variables():
    """Проверяет переменные окружения"""
    print("\n🔍 Проверка переменных окружения...")
    
    # Проверяем все возможные источники
    sources = [
        ('os.getenv', os.getenv('YANDEX_SPEECHKIT_API_KEY'), os.getenv('YANDEX_FOLDER_ID')),
        ('config_veretevo.env', YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID),
    ]
    
    for source_name, api_key, folder_id in sources:
        print(f"📋 {source_name}:")
        print(f"   API Key: {'УСТАНОВЛЕН' if api_key else 'НЕ УСТАНОВЛЕН'}")
        print(f"   Folder ID: {folder_id}")
        if api_key:
            print(f"   API Key (первые 10 символов): {api_key[:10]}...")

def main():
    print("🚀 Диагностика API ключей и folder ID\n")
    
    # Проверяем переменные окружения
    check_environment_variables()
    
    # Тестируем API с разными учетными данными
    test_api_with_different_credentials()
    
    print("\n📋 Рекомендации:")
    print("1. Проверьте, что API ключ действителен для указанного folder ID")
    print("2. Убедитесь, что в Yandex Cloud включен SpeechKit")
    print("3. Проверьте баланс в Yandex Cloud Console")
    print("4. Попробуйте создать новый API ключ")

if __name__ == "__main__":
    main()
