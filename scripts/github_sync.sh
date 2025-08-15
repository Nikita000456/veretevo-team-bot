#!/bin/bash

# Скрипт для автоматической синхронизации с GitHub
# Использование: ./scripts/github_sync.sh [commit_message]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    error "Скрипт должен запускаться из корневой папки проекта"
    exit 1
fi

# Проверяем статус Git
log "Проверяем статус Git..."
if ! git status --porcelain | grep -q .; then
    warning "Нет изменений для коммита"
    exit 0
fi

# Получаем сообщение коммита
COMMIT_MESSAGE=${1:-"Auto-sync: $(date +'%Y-%m-%d %H:%M:%S')"}

# Добавляем все изменения
log "Добавляем изменения в Git..."
git add .

# Создаем коммит
log "Создаем коммит: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# Отправляем на GitHub
log "Отправляем изменения на GitHub..."
git push origin main

log "✅ Синхронизация завершена успешно!"

# Проверяем статус бота
log "Проверяем статус бота..."
if systemctl is-active --quiet veretevo-bot; then
    log "✅ Бот работает"
else
    warning "⚠️ Бот не запущен"
fi

# Показываем последние логи
log "Последние логи бота:"
tail -5 logs/bot.log 2>/dev/null || echo "Логи не найдены" 