#!/bin/bash
# Скрипт для быстрой проверки статуса Veretevo Team Bot

echo "📊 === СТАТУС VERETEVO TEAM BOT ==="
echo "⏰ Время проверки: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Проверяем статус systemd сервиса
echo "🔍 Проверка systemd сервиса..."
if sudo systemctl is-active --quiet veretevo-bot; then
    echo "✅ Сервис активен"
else
    echo "❌ Сервис не активен"
fi

# Проверяем процесс Python
echo "🐍 Проверка процесса Python..."
PYTHON_PID=$(pgrep -f "python3 main.py")
if [ -n "$PYTHON_PID" ]; then
    echo "✅ Процесс Python найден (PID: $PYTHON_PID)"
    
    # Проверяем время работы процесса
    UPTIME=$(ps -o etime= -p $PYTHON_PID 2>/dev/null)
    if [ -n "$UPTIME" ]; then
        echo "⏱️  Время работы: $UPTIME"
    fi
    
    # Проверяем использование памяти
    MEMORY=$(ps -o rss= -p $PYTHON_PID 2>/dev/null)
    if [ -n "$MEMORY" ]; then
        MEMORY_MB=$((MEMORY / 1024))
        echo "💾 Использование памяти: ${MEMORY_MB}MB"
    fi
else
    echo "❌ Процесс Python не найден"
fi

echo ""

# Показываем последние логи
echo "📋 Последние записи в логах:"
if [ -f "logs/bot.log" ]; then
    echo "📄 Файл logs/bot.log:"
    tail -3 logs/bot.log | sed 's/^/   /'
else
    echo "❌ Файл логов не найден"
fi

echo ""

# Показываем статус systemd
echo "📋 Статус systemd сервиса:"
sudo systemctl status veretevo-bot --no-pager -l | head -8 