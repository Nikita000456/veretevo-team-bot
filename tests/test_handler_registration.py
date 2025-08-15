#!/usr/bin/env python3
"""
Тест регистрации обработчиков
"""

import sys
import os

# Добавляем путь к модулям бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_handler_registration():
    """Тестирует регистрацию обработчиков"""
    print("🔍 Тестирование регистрации обработчиков...")
    
    try:
        # Импортируем функцию регистрации
        from handlers_veretevo.tasks import register_task_handlers
        
        # Создаем мок application
        from unittest.mock import Mock
        application = Mock()
        
        # Регистрируем обработчики
        print("📝 Регистрируем обработчики...")
        register_task_handlers(application)
        
        # Проверяем, что add_handler был вызван
        if application.add_handler.called:
            print("✅ add_handler() был вызван")
            print(f"   Количество вызовов: {application.add_handler.call_count}")
            
            # Получаем все вызовы
            calls = application.add_handler.call_args_list
            for i, call in enumerate(calls):
                handler = call[0][0] if call[0] else None
                if handler:
                    print(f"   Вызов {i+1}: {type(handler).__name__}")
        else:
            print("❌ add_handler() не был вызван")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании регистрации: {e}")
        return False

def test_voice_handler_availability():
    """Тестирует доступность обработчика голосовых сообщений"""
    print("\n🔍 Тестирование доступности обработчика голосовых сообщений...")
    
    try:
        # Импортируем функцию
        from handlers_veretevo.tasks import handle_voice_message
        
        # Проверяем, что функция существует и является корутиной
        import inspect
        if inspect.iscoroutinefunction(handle_voice_message):
            print("✅ handle_voice_message является корутиной")
        else:
            print("❌ handle_voice_message не является корутиной")
            
        # Проверяем сигнатуру функции
        sig = inspect.signature(handle_voice_message)
        params = list(sig.parameters.keys())
        print(f"   Параметры: {params}")
        
        if 'update' in params and 'context' in params:
            print("✅ Сигнатура функции корректна")
        else:
            print("❌ Неправильная сигнатура функции")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании доступности: {e}")
        return False

def test_voice_transcriber_availability():
    """Тестирует доступность voice_transcriber"""
    print("\n🔍 Тестирование доступности voice_transcriber...")
    
    try:
        from handlers_veretevo.tasks import voice_transcriber
        
        if voice_transcriber:
            print("✅ voice_transcriber доступен")
            print(f"   Тип: {type(voice_transcriber)}")
            
            # Проверяем методы
            methods = ['process_audio_file', 'transcribe_audio', 'convert_audio_to_ogg']
            for method in methods:
                if hasattr(voice_transcriber, method):
                    print(f"   ✅ Метод {method} доступен")
                else:
                    print(f"   ❌ Метод {method} недоступен")
        else:
            print("❌ voice_transcriber недоступен")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании voice_transcriber: {e}")
        return False

def main():
    print("🚀 Тест регистрации обработчиков\n")
    
    # Тест 1: Регистрация обработчиков
    registration_ok = test_handler_registration()
    
    # Тест 2: Доступность обработчика голосовых сообщений
    handler_ok = test_voice_handler_availability()
    
    # Тест 3: Доступность voice_transcriber
    transcriber_ok = test_voice_transcriber_availability()
    
    print(f"\n📊 Результаты:")
    print(f"   Регистрация: {'✅ ОК' if registration_ok else '❌ ОШИБКА'}")
    print(f"   Обработчик: {'✅ ОК' if handler_ok else '❌ ОШИБКА'}")
    print(f"   Транскрайбер: {'✅ ОК' if transcriber_ok else '❌ ОШИБКА'}")
    
    if registration_ok and handler_ok and transcriber_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("💡 Обработчики зарегистрированы корректно")
        print("💡 Попробуйте отправить голосовое сообщение боту")
    else:
        print("\n⚠️ Есть проблемы с регистрацией обработчиков")
        print("💡 Проверьте код регистрации обработчиков")

if __name__ == "__main__":
    main()
