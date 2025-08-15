#!/usr/bin/env python3
"""
Детальная отладка API Yandex SpeechKit
"""

import os
import tempfile
import requests
import json
from pydub.generators import Sine

def test_api_credentials():
    """Тестирует учетные данные API"""
    print("🔍 Тестирование учетных данных API...")
    
    try:
        from config_veretevo.env import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID
        
        print(f"API Key: {'УСТАНОВЛЕН' if YANDEX_SPEECHKIT_API_KEY else 'НЕ УСТАНОВЛЕН'}")
        if YANDEX_SPEECHKIT_API_KEY:
            print(f"   Длина: {len(YANDEX_SPEECHKIT_API_KEY)} символов")
            print(f"   Начинается с: {YANDEX_SPEECHKIT_API_KEY[:10]}...")
        
        print(f"Folder ID: {'УСТАНОВЛЕН' if YANDEX_FOLDER_ID else 'НЕ УСТАНОВЛЕН'}")
        if YANDEX_FOLDER_ID:
            print(f"   Значение: {YANDEX_FOLDER_ID}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке учетных данных: {e}")
        return False

def test_api_connection():
    """Тестирует подключение к API"""
    print("\n🔍 Тестирование подключения к API...")
    
    try:
        from config_veretevo.env import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID
        
        if not YANDEX_SPEECHKIT_API_KEY or not YANDEX_FOLDER_ID:
            print("❌ Учетные данные не установлены")
            return False
            
        # Создаем простой тестовый файл
        tone = Sine(440).to_audio_segment(duration=2000)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            tone.export(temp_file.name, format='ogg', codec='libopus', 
                       parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            
            print(f"✅ Тестовый файл создан: {temp_file.name}")
            print(f"📊 Размер файла: {os.path.getsize(temp_file.name)} байт")
            
            # Тестируем API
            url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?folderId={YANDEX_FOLDER_ID}&lang=ru-RU&model=general:rc&sampleRateHertz=48000&profanityFilter=false&partialResults=false"
            headers = {
                'Authorization': f'Api-Key {YANDEX_SPEECHKIT_API_KEY}',
                'Content-Type': 'application/octet-stream'
            }
            
            print(f"🔗 URL: {url}")
            print(f"🔑 API Key: {YANDEX_SPEECHKIT_API_KEY[:10]}...")
            print(f"📁 Folder ID: {YANDEX_FOLDER_ID}")
            print(f"📋 Headers: {headers}")
            
            with open(temp_file.name, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            print(f"📊 Размер данных: {len(audio_data)} байт")
            print(f"📊 Первые 50 байт: {audio_data[:50]}")
            
            print("🚀 Отправляем запрос к API...")
            response = requests.post(url, headers=headers, data=audio_data, timeout=30)
            
            print(f"📡 Статус ответа: {response.status_code}")
            print(f"📋 Заголовки ответа: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Успешный ответ: {result}")
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"📄 Текст ответа: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании API: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def test_different_api_endpoints():
    """Тестирует разные эндпоинты API"""
    print("\n🔍 Тестирование разных эндпоинтов API...")
    
    try:
        from config_veretevo.env import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID
        
        if not YANDEX_SPEECHKIT_API_KEY or not YANDEX_FOLDER_ID:
            print("❌ Учетные данные не установлены")
            return False
            
        # Создаем тестовый файл
        tone = Sine(440).to_audio_segment(duration=1000)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
            tone.export(temp_file.name, format='ogg', codec='libopus', 
                       parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
            
            with open(temp_file.name, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            headers = {
                'Authorization': f'Api-Key {YANDEX_SPEECHKIT_API_KEY}',
                'Content-Type': 'application/octet-stream'
            }
            
            # Тест 1: Базовый эндпоинт
            print("🎤 Тест 1: Базовый эндпоинт...")
            url1 = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?folderId={YANDEX_FOLDER_ID}&lang=ru-RU"
            response1 = requests.post(url1, headers=headers, data=audio_data, timeout=10)
            print(f"   Статус: {response1.status_code}")
            print(f"   Ответ: {response1.text[:200]}...")
            
            # Тест 2: С дополнительными параметрами
            print("🎤 Тест 2: С дополнительными параметрами...")
            url2 = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?folderId={YANDEX_FOLDER_ID}&lang=ru-RU&model=general:rc&sampleRateHertz=48000"
            response2 = requests.post(url2, headers=headers, data=audio_data, timeout=10)
            print(f"   Статус: {response2.status_code}")
            print(f"   Ответ: {response2.text[:200]}...")
            
            # Тест 3: Проверка авторизации
            print("🎤 Тест 3: Проверка авторизации...")
            url3 = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
            response3 = requests.post(url3, headers=headers, data=audio_data, timeout=10)
            print(f"   Статус: {response3.status_code}")
            print(f"   Ответ: {response3.text[:200]}...")
            
            os.unlink(temp_file.name)
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании эндпоинтов: {e}")

def main():
    print("🚀 Детальная отладка API Yandex SpeechKit\n")
    
    # Тест 1: Учетные данные
    credentials_ok = test_api_credentials()
    
    # Тест 2: Подключение к API
    connection_ok = test_api_connection()
    
    # Тест 3: Разные эндпоинты
    test_different_api_endpoints()
    
    print(f"\n📊 Результаты:")
    print(f"   Учетные данные: {'✅ ОК' if credentials_ok else '❌ ОШИБКА'}")
    print(f"   Подключение: {'✅ ОК' if connection_ok else '❌ ОШИБКА'}")
    
    if credentials_ok and connection_ok:
        print("\n🎉 API работает корректно!")
    else:
        print("\n⚠️ Есть проблемы с API")
        print("💡 Проверьте учетные данные и подключение к интернету")

if __name__ == "__main__":
    main()
