#!/bin/bash

# Универсальный скрипт для перезапуска Veretevo Team Bot
# Использование: ./restart-bot.sh [сообщение] [--quick|--full|--manual]
# --quick: только перезапуск сервиса (быстро)
# --full: синхронизация с GitHub + перезапуск (по умолчанию)
# --manual: ручной запуск без systemd

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    error "Скрипт должен запускаться из корневой папки проекта"
    exit 1
fi

# Парсим аргументы
COMMIT_MESSAGE=${1:-"Перезагрузка VeretevoTeam бота - $(date)"}
MODE=${2:-"--full"}

# Функция для проверки статуса сервиса
check_service_status() {
    echo "📊 Проверяю текущий статус сервиса..."
    if sudo systemctl is-active --quiet veretevo-bot; then
        echo "✅ Сервис активен"
        CURRENT_PID=$(pgrep -f "python3 main.py")
        if [ -n "$CURRENT_PID" ]; then
            echo "🔍 Найден процесс Python (PID: $CURRENT_PID)"
        fi
    else
        echo "❌ Сервис не активен"
    fi
    echo ""
}

# Функция для остановки сервиса
stop_service() {
    echo "🛑 Останавливаю сервис veretevo-bot..."
    sudo systemctl stop veretevo-bot
    STOP_RESULT=$?

    if [ $STOP_RESULT -eq 0 ]; then
        echo "✅ Сервис успешно остановлен"
    else
        echo "⚠️  Сервис остановлен с предупреждениями"
    fi

    # Ждем завершения процессов
    echo "⏳ Ожидаю завершения процессов..."
    for i in {1..5}; do
        if ! pgrep -f "python3 main.py" > /dev/null; then
            echo "✅ Все процессы завершены"
            break
        fi
        echo "⏳ Ожидание... ($i/5)"
        sleep 1
    done

    # Принудительно завершаем, если процессы все еще живут
    if pgrep -f "python3 main.py" > /dev/null; then
        echo "🔨 Принудительное завершение процессов..."
        sudo pkill -f "python3 main.py"
        sleep 2
    fi
    echo ""
}

# Функция для запуска сервиса
start_service() {
    echo "🚀 Запускаю сервис veretevo-bot..."
    sudo systemctl start veretevo-bot
    START_RESULT=$?

    if [ $START_RESULT -eq 0 ]; then
        echo "✅ Команда запуска выполнена успешно"
    else
        echo "❌ Ошибка при запуске сервиса"
        exit 1
    fi

    # Ждем инициализации
    echo "⏳ Ожидаю инициализации бота..."
    for i in {1..10}; do
        if sudo systemctl is-active --quiet veretevo-bot; then
            echo "✅ Сервис активен"
            break
        fi
        echo "⏳ Ожидание инициализации... ($i/10)"
        sleep 1
    done
}

# Функция для проверки финального статуса
check_final_status() {
    echo ""
    echo "📊 Проверяю финальный статус..."
    if sudo systemctl is-active --quiet veretevo-bot; then
        echo "✅ Бот успешно запущен!"
        NEW_PID=$(pgrep -f "python3 main.py")
        if [ -n "$NEW_PID" ]; then
            echo "🔍 Новый процесс Python (PID: $NEW_PID)"
        fi
        
        # Запускаем проверку совместимости если скрипт существует
        if [ -f "scripts/compatibility_check.py" ]; then
            echo ""
            echo "🔍 Проверка совместимости..."
            python3 scripts/compatibility_check.py
            COMPATIBILITY_RESULT=$?
            
            if [ $COMPATIBILITY_RESULT -eq 0 ]; then
                echo "✅ Совместимость подтверждена"
            else
                echo "⚠️  Обнаружены проблемы совместимости"
            fi
        fi
        
        echo "⏰ Время завершения: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "🎉 Перезапуск завершен успешно!"
    else
        echo "❌ Ошибка: сервис не активен"
        echo "📋 Логи сервиса:"
        sudo journalctl -u veretevo-bot -n 10 --no-pager
        exit 1
    fi

    echo ""
    echo "📋 Краткий статус сервиса:"
    sudo systemctl status veretevo-bot --no-pager -l | head -10
}

# Функция для ручного запуска
manual_start() {
    echo "🔄 === РУЧНОЙ ЗАПУСК VERETEVO TEAM BOT ==="
    echo "⏰ Время начала: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Завершаем предыдущий процесс бота, если он есть
    PID=$(pgrep -f "python3 main.py")
    if [ -n "$PID" ]; then
        echo "Останавливаю предыдущий процесс Veretevo Team Bot (PID $PID)"
        kill -TERM $PID
        
        # Ждем максимум 10 секунд для graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                echo "Процесс успешно завершен"
                break
            fi
            echo "Ожидание завершения процесса... ($i/10)"
            sleep 1
        done
        
        # Принудительно завершаем, если процесс все еще жив
        if kill -0 $PID 2>/dev/null; then
            echo "Принудительное завершение процесса"
            kill -KILL $PID
            sleep 1
        fi
    fi

    # Проверяем, что процесс действительно завершен
    if pgrep -f "python3 main.py" > /dev/null; then
        echo "ОШИБКА: Не удалось завершить процесс"
        exit 1
    fi

    echo "Активация виртуального окружения..."
    source venv/bin/activate

    echo "Установка переменных окружения..."
    export TELEGRAM_TOKEN="7705651037:AAEgIhvMAiqVAle0lqdbZ_rnicrJM_tN_B4"

    echo "Создание директории для логов..."
    mkdir -p logs

    echo "Запуск бота..."
    # Запускаем бота в foreground режиме
    python3 main.py
}

# Основная логика
case $MODE in
    "--quick")
        log "🚀 Быстрый перезапуск VeretevoTeam бота"
        check_service_status
        stop_service
        start_service
        check_final_status
        log "✅ Быстрый перезапуск завершен!"
        ;;
    "--manual")
        manual_start
        ;;
    "--full"|*)
        log "🚀 Запуск полной перезагрузки VeretevoTeam бота"
        log "📝 Сообщение: $COMMIT_MESSAGE"
        
        # Шаг 1: Синхронизация с GitHub
        log "📤 Шаг 1: Синхронизация с GitHub..."
        if [ -f "scripts/github_sync.sh" ]; then
            ./scripts/github_sync.sh "$COMMIT_MESSAGE"
        else
            warning "Скрипт github_sync.sh не найден, пропускаю синхронизацию"
        fi
        
        # Шаг 2: Перезагрузка бота
        log "🔄 Шаг 2: Перезагрузка бота..."
        check_service_status
        stop_service
        start_service
        check_final_status
        
        log "✅ Полная перезагрузка завершена!"
        log "📱 Проверьте уведомление в Telegram"
        log "🔗 GitHub Actions: https://github.com/Nikita000456/veretevo-team-bot/actions"
        ;;
esac 