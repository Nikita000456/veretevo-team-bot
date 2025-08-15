#!/bin/bash

# Скрипт для управления резервными копиями проекта VeretevoTeam
# Автор: AI Assistant

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"

show_help() {
    echo "🔧 Управление резервными копиями VeretevoTeam"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  create    - Создать новую резервную копию"
    echo "  list      - Показать все резервные копии"
    echo "  restore   - Восстановить из резервной копии"
    echo "  clean     - Удалить старые резервные копии (оставить последние 5)"
    echo "  info      - Показать информацию о резервных копиях"
    echo "  help      - Показать эту справку"
    echo ""
}

list_backups() {
    echo "📋 Список резервных копий:"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR"/*.tar.gz 2>/dev/null)" ]; then
        ls -lah "$BACKUP_DIR"/*.tar.gz | while read -r line; do
            echo "  $line"
        done
    else
        echo "  Нет резервных копий"
    fi
}

create_backup() {
    echo "🔧 Создание новой резервной копии..."
    "$PROJECT_DIR/scripts/backup_project.sh"
}

restore_backup() {
    if [ -z "$1" ]; then
        echo "❌ Ошибка: Укажите имя файла резервной копии"
        echo "Пример: $0 restore veretevo_backup_20250728_005355.tar.gz"
        exit 1
    fi
    
    BACKUP_FILE="$BACKUP_DIR/$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Ошибка: Файл $BACKUP_FILE не найден"
        exit 1
    fi
    
    echo "🔄 Восстановление из резервной копии: $1"
    echo "⚠️  ВНИМАНИЕ: Это перезапишет текущие файлы!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Распаковка архива..."
        cd "$PROJECT_DIR"
        tar -xzf "$BACKUP_FILE"
        
        # Перемещаем файлы из распакованной папки
        BACKUP_NAME=$(basename "$1" .tar.gz)
        if [ -d "$BACKUP_NAME" ]; then
            echo "📁 Копирование файлов..."
            cp -r "$BACKUP_NAME"/* .
            rm -rf "$BACKUP_NAME"
            echo "✅ Восстановление завершено!"
        else
            echo "❌ Ошибка при распаковке"
            exit 1
        fi
    else
        echo "❌ Восстановление отменено"
    fi
}

clean_backups() {
    echo "🧹 Очистка старых резервных копий..."
    if [ -d "$BACKUP_DIR" ]; then
        # Оставляем только последние 5 бэкапов
        BACKUP_COUNT=$(ls "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
        if [ "$BACKUP_COUNT" -gt 5 ]; then
            echo "Удаление старых резервных копий..."
            ls -t "$BACKUP_DIR"/*.tar.gz | tail -n +6 | xargs rm -f
            echo "✅ Удалено $((BACKUP_COUNT - 5)) старых резервных копий"
        else
            echo "ℹ️  Количество резервных копий в пределах нормы ($BACKUP_COUNT)"
        fi
    fi
}

show_info() {
    echo "📊 Информация о резервных копиях:"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(ls "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
        TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
        
        echo "📁 Директория: $BACKUP_DIR"
        echo "📦 Количество: $BACKUP_COUNT"
        echo "💾 Общий размер: $TOTAL_SIZE"
        echo ""
        
        if [ "$BACKUP_COUNT" -gt 0 ]; then
            echo "📋 Последние резервные копии:"
            ls -lah "$BACKUP_DIR"/*.tar.gz | tail -5 | while read -r line; do
                echo "  $line"
            done
        fi
    else
        echo "📁 Директория резервных копий не существует"
    fi
}

# Основная логика
case "${1:-help}" in
    "create")
        create_backup
        ;;
    "list")
        list_backups
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "clean")
        clean_backups
        ;;
    "info")
        show_info
        ;;
    "help"|*)
        show_help
        ;;
esac 