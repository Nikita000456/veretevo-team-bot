#!/usr/bin/env python3
"""
Мониторинг логов бота для отслеживания голосовых сообщений
"""

import os
import sys
import time
import subprocess

def monitor_logs():
    """Мониторит логи бота в реальном времени"""
    print("🔍 Мониторинг логов бота для голосовых сообщений...")
    print("📝 Отправьте голосовое сообщение в чат ассистентов")
    print("🔄 Логи обновляются в реальном времени...")
    print("⏹️  Для остановки нажмите Ctrl+C\n")
    
    try:
        # Запускаем tail -f для мониторинга логов
        cmd = ["tail", "-f", "logs/bot.log"]
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Фильтруем только записи, связанные с голосовыми сообщениями
        keywords = [
            "голосовое", "voice", "транскрипция", "speech", 
            "DEBUG.*voice", "handle_voice_message", "voice_transcriber"
        ]
        
        for line in process.stdout:
            # Проверяем, содержит ли строка ключевые слова
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in keywords):
                print(f"🎤 {line.strip()}")
            elif "error" in line_lower or "ошибка" in line_lower:
                print(f"❌ {line.strip()}")
            elif "debug" in line_lower:
                print(f"🔍 {line.strip()}")
                
    except KeyboardInterrupt:
        print("\n⏹️  Мониторинг остановлен")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")

if __name__ == "__main__":
    # Проверяем, что мы в правильной директории
    if not os.path.exists("logs/bot.log"):
        print("❌ Файл logs/bot.log не найден")
        print("💡 Убедитесь, что вы находитесь в директории бота")
        sys.exit(1)
    
    print("🚀 Запуск мониторинга логов бота...")
    monitor_logs() 