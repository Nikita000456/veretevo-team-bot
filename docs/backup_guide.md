# 📋 Руководство по резервному копированию проекта VeretevoTeam

## Обзор

Этот документ описывает систему резервного копирования проекта VeretevoTeam, которая позволяет создавать, управлять и восстанавливать резервные копии всего проекта.

## 🎯 Цели резервного копирования

- **Безопасность данных**: Защита от потери кода и конфигураций
- **Версионность**: Возможность отката к предыдущим версиям
- **Переносимость**: Легкое развертывание на новых серверах
- **Документирование**: Сохранение истории изменений

## 📁 Структура резервных копий

```
backups/
├── veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
├── veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
└── ...
```

## 🔧 Автоматические скрипты

### 1. Создание резервной копии

```bash
# Создать новую резервную копию
./scripts/backup_project.sh

# Или через скрипт управления
./scripts/manage_backups.sh create
```

### 2. Управление резервными копиями

```bash
# Показать справку
./scripts/manage_backups.sh help

# Список всех резервных копий
./scripts/manage_backups.sh list

# Информация о резервных копиях
./scripts/manage_backups.sh info

# Очистка старых резервных копий (оставить последние 5)
./scripts/manage_backups.sh clean
```

### 3. Восстановление из резервной копии

```bash
# Восстановить из конкретной резервной копии
./scripts/manage_backups.sh restore veretevo_backup_20250728_005355.tar.gz
```

## 📦 Содержимое резервной копии

### Основные файлы
- `main.py` - Главный файл бота
- `requirements.txt` - Зависимости Python
- `README.md` - Документация проекта
- `run_veretevo.sh` - Скрипт запуска
- `run_tests.sh` - Скрипт тестирования
- `quick_restart.sh` - Быстрый перезапуск
- `veretevo-bot.service` - Systemd сервис
- `.gitignore` - Исключения Git

### Директории
- `handlers_veretevo/` - Обработчики команд
- `services_veretevo/` - Бизнес-логика
- `config_veretevo/` - Конфигурации
- `utils_veretevo/` - Утилиты
- `docs/` - Документация
- `scripts/` - Скрипты
- `tests/` - Тесты
- `data/` - Данные

## 🔄 Процесс восстановления

### Автоматическое восстановление

1. **Выберите резервную копию**:
   ```bash
   ./scripts/manage_backups.sh list
   ```

2. **Восстановите проект**:
   ```bash
   ./scripts/manage_backups.sh restore veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

3. **Подтвердите восстановление** (введите 'y')

### Ручное восстановление

1. **Распакуйте архив**:
   ```bash
   tar -xzf backups/veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

2. **Скопируйте файлы**:
   ```bash
   cp -r veretevo_backup_YYYYMMDD_HHMMSS/* .
   ```

3. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте конфигурацию**:
   ```bash
   # Отредактируйте файлы в config_veretevo/
   ```

## ⚙️ Настройка автоматического резервного копирования

### Cron задача (ежедневно в 2:00)

```bash
# Добавить в crontab
0 2 * * * cd /home/ubuntu/testbot/VeretevoTeam && ./scripts/backup_project.sh
```

### Systemd таймер (рекомендуется)

Создайте файл `/etc/systemd/system/veretevo-backup.timer`:

```ini
[Unit]
Description=VeretevoTeam Backup Timer
Requires=veretevo-backup.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

И файл `/etc/systemd/system/veretevo-backup.service`:

```ini
[Unit]
Description=VeretevoTeam Backup Service
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/testbot/VeretevoTeam
ExecStart=/home/ubuntu/testbot/VeretevoTeam/scripts/backup_project.sh

[Install]
WantedBy=multi-user.target
```

Затем активируйте:

```bash
sudo systemctl enable veretevo-backup.timer
sudo systemctl start veretevo-backup.timer
```

## 📊 Мониторинг резервных копий

### Проверка статуса

```bash
# Информация о резервных копиях
./scripts/manage_backups.sh info

# Проверка размера
du -sh backups/

# Проверка целостности архива
tar -tzf backups/veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Логирование

Резервные копии создаются с временными метками и информацией о системе:

- Дата и время создания
- Версия Git (если доступна)
- Размер архива
- Список включенных файлов

## 🛡️ Безопасность

### Рекомендации

1. **Храните резервные копии в разных местах**:
   - Локальный сервер
   - Облачное хранилище
   - Внешний диск

2. **Шифруйте чувствительные данные**:
   ```bash
   # Создание зашифрованного архива
   tar -czf - . | gpg -e -r your-email@example.com > backup_encrypted.tar.gz.gpg
   ```

3. **Регулярно тестируйте восстановление**:
   ```bash
   # Тест восстановления в отдельной директории
   mkdir test_restore
   cd test_restore
   tar -xzf ../backups/veretevo_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

## 🔧 Устранение неполадок

### Проблемы при создании резервной копии

```bash
# Проверка прав доступа
ls -la scripts/backup_project.sh

# Проверка свободного места
df -h

# Проверка зависимостей
which tar
which gzip
```

### Проблемы при восстановлении

```bash
# Проверка целостности архива
tar -tzf backups/veretevo_backup_YYYYMMDD_HHMMSS.tar.gz

# Проверка свободного места
df -h

# Проверка прав доступа
ls -la backups/
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f logs_veretevo/backup.log`
2. Проверьте права доступа к файлам
3. Убедитесь в достаточном количестве свободного места
4. Проверьте целостность архивов

---

**Дата создания**: 28 июля 2025  
**Версия документа**: 1.0  
**Автор**: AI Assistant 