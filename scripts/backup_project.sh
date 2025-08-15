#!/bin/bash

# Скрипт для создания резервной копии проекта VeretevoTeam
# Автор: AI Assistant
# Дата создания: $(date)

set -e

# Настройки
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="veretevo_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "🔧 Создание резервной копии проекта VeretevoTeam..."
echo "📁 Проект: $PROJECT_DIR"
echo "💾 Резервная копия: $BACKUP_PATH"

# Создаем директорию для бэкапа
mkdir -p "$BACKUP_PATH"

# Список важных файлов и папок для бэкапа
IMPORTANT_FILES=(
    "main.py"
    "requirements.txt"
    "README.md"
    "run_veretevo.sh"
    "run_tests.sh"
    "restart-bot.sh"
    "veretevo-bot.service"
    ".gitignore"
)

IMPORTANT_DIRS=(
    "handlers_veretevo"
    "services_veretevo"
    "config_veretevo"
    "utils_veretevo"
    "docs"
    "scripts"
    "tests"
    "data"
)

# Копируем важные файлы
echo "📄 Копирование важных файлов..."
for file in "${IMPORTANT_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        cp "$PROJECT_DIR/$file" "$BACKUP_PATH/"
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file (не найден)"
    fi
done

# Копируем важные директории
echo "📁 Копирование важных директорий..."
for dir in "${IMPORTANT_DIRS[@]}"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        cp -r "$PROJECT_DIR/$dir" "$BACKUP_PATH/"
        echo "  ✅ $dir/"
    else
        echo "  ⚠️  $dir/ (не найдена)"
    fi
done

# Создаем файл с информацией о бэкапе
cat > "$BACKUP_PATH/backup_info.txt" << EOF
Резервная копия проекта VeretevoTeam
====================================

Дата создания: $(date)
Версия: $(git describe --tags 2>/dev/null || echo "Неизвестно")
Коммит: $(git rev-parse HEAD 2>/dev/null || echo "Неизвестно")

Содержимое бэкапа:
- Основные файлы проекта
- Обработчики (handlers_veretevo)
- Сервисы (services_veretevo)
- Конфигурации (config_veretevo)
- Утилиты (utils_veretevo)
- Документация (docs)
- Скрипты (scripts)
- Тесты (tests)
- Данные (data)

Для восстановления:
1. Скопируйте содержимое этой папки в новую директорию
2. Установите зависимости: pip install -r requirements.txt
3. Настройте конфигурацию в config_veretevo/
4. Запустите: python main.py

EOF

# Создаем архив
echo "🗜️  Создание архива..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo "✅ Резервная копия создана успешно!"
echo "📦 Архив: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "📊 Размер: $(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)"

# Показываем список всех бэкапов
echo ""
echo "📋 Все резервные копии:"
ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "  Нет резервных копий"

echo ""
echo "�� Бэкап завершен!" 