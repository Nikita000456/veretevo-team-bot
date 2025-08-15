#!/bin/bash

# Скрипт для автоматического уведомления пользователей о обновлениях при деплое
# Использование: ./scripts/deploy_notify.sh [версия] [описание]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверяем аргументы
if [ $# -lt 2 ]; then
    echo "Использование: $0 <версия> <описание>"
    echo "Пример: $0 \"v1.2.0\" \"Добавлены новые функции в меню\""
    exit 1
fi

VERSION="$1"
DESCRIPTION="$2"

# Переходим в директорию проекта
cd "$(dirname "$0")/.."

log "Начинаем процесс уведомления о обновлении..."

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    error "Скрипт должен запускаться из корневой директории проекта"
    exit 1
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    warning "Виртуальное окружение не найдено. Создаем..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
log "Активируем виртуальное окружение..."
source venv/bin/activate

# Проверяем зависимости
log "Проверяем зависимости..."
pip install -r requirements.txt > /dev/null 2>&1

# Формируем сообщение об обновлении
UPDATE_TITLE="Обновление бота v${VERSION}"
UPDATE_MESSAGE="Версия ${VERSION} была успешно развернута на сервере.\n\n${DESCRIPTION}\n\nОтправьте /start для обновления меню."

# Отправляем уведомление
log "Отправляем уведомление пользователям..."
python scripts/auto_notify.py update "$UPDATE_TITLE" "$UPDATE_MESSAGE"

if [ $? -eq 0 ]; then
    success "Уведомление об обновлении успешно отправлено!"
    
    # Показываем статистику
    log "Получаем статистику пользователей..."
    python scripts/auto_notify.py stats
    
else
    error "Ошибка при отправке уведомления"
    exit 1
fi

# Очистка неактивных пользователей (раз в неделю)
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" = "1" ]; then  # Понедельник
    log "Выполняем еженедельную очистку неактивных пользователей..."
    python scripts/auto_notify.py cleanup
fi

success "Процесс уведомления завершен!"

# Деактивируем виртуальное окружение
deactivate 