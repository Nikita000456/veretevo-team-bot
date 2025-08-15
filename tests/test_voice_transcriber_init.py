#!/usr/bin/env python3
"""
Тест инициализации voice_transcriber в контексте бота
"""

import sys
import os

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_voice_transcriber_initialization():
    """Тестирует инициализацию voice_transcriber"""
    print("🔍 Тестирование инициализации voice_transcriber...")
    
    try:
        # Импортируем модуль tasks
        from handlers_veretevo.tasks import voice_transcriber
        
        if voice_transcriber:
            print("✅ voice_transcriber инициализирован успешно")
            print(f"   Тип: {type(voice_transcriber)}")
            
            # Проверяем атрибуты
            if hasattr(voice_transcriber, 'api_key'):
                print(f"   API Key: {'УСТАНОВЛЕН' if voice_transcriber.api_key else 'НЕ УСТАНОВЛЕН'}")
            else:
                print("   ❌ API Key не найден")
                
            if hasattr(voice_transcriber, 'folder_id'):
                print(f"   Folder ID: {'УСТАНОВЛЕН' if voice_transcriber.folder_id else 'НЕ УСТАНОВЛЕН'}")
            else:
                print("   ❌ Folder ID не найден")
                
            return True
        else:
            print("❌ voice_transcriber равен None")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        return False

def test_import_structure():
    """Тестирует структуру импортов"""
    print("\n🔍 Тестирование структуры импортов...")
    
    try:
        # Проверяем импорт YandexSpeechKitTranscriber
        from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber
        print("✅ YandexSpeechKitTranscriber импортирован успешно")
        
        # Проверяем импорт config_veretevo
        from config_veretevo import env
        print("✅ config_veretevo.env импортирован успешно")
        
        # Проверяем переменные окружения
        api_key = env.YANDEX_SPEECHKIT_API_KEY
        folder_id = env.YANDEX_FOLDER_ID
        
        print(f"   API Key из env: {'УСТАНОВЛЕН' if api_key else 'НЕ УСТАНОВЛЕН'}")
        print(f"   Folder ID из env: {'УСТАНОВЛЕН' if folder_id else 'НЕ УСТАНОВЛЕН'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
        return False

def test_voice_transcriber_methods():
    """Тестирует методы voice_transcriber"""
    print("\n🔍 Тестирование методов voice_transcriber...")
    
    try:
        from handlers_veretevo.tasks import voice_transcriber
        
        if not voice_transcriber:
            print("❌ voice_transcriber не инициализирован")
            return False
            
        # Проверяем наличие методов
        methods = ['process_audio_file', 'transcribe_audio', 'convert_audio_to_ogg', 'test_connection']
        
        for method in methods:
            if hasattr(voice_transcriber, method):
                print(f"✅ Метод {method} найден")
            else:
                print(f"❌ Метод {method} не найден")
                
        # Тестируем test_connection
        if hasattr(voice_transcriber, 'test_connection'):
            print("🔗 Тестируем подключение к API...")
            result = voice_transcriber.test_connection()
            print(f"   Результат: {'✅ УСПЕХ' if result else '❌ ПРОВАЛ'}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании методов: {e}")
        return False

def main():
    print("🚀 Тест инициализации voice_transcriber\n")
    
    # Тест 1: Структура импортов
    import_ok = test_import_structure()
    
    # Тест 2: Инициализация voice_transcriber
    init_ok = test_voice_transcriber_initialization()
    
    # Тест 3: Методы voice_transcriber
    methods_ok = test_voice_transcriber_methods()
    
    print(f"\n📊 Результаты:")
    print(f"   Импорты: {'✅ ОК' if import_ok else '❌ ОШИБКА'}")
    print(f"   Инициализация: {'✅ ОК' if init_ok else '❌ ОШИБКА'}")
    print(f"   Методы: {'✅ ОК' if methods_ok else '❌ ОШИБКА'}")
    
    if import_ok and init_ok and methods_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("💡 voice_transcriber должен работать в боте")
    else:
        print("\n⚠️ Есть проблемы с voice_transcriber")
        print("💡 Проверьте конфигурацию и перезапустите бота")

if __name__ == "__main__":
    main()
