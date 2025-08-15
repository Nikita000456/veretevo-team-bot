# Структура проекта VeretevoTeam

## Организация файлов

Проект организован по следующим папкам:

### 📁 Основные папки

- **`main.py`** - главный файл бота
- **`config/`** - конфигурационные файлы
  - `veretevo-bot.service` - systemd сервис
  - `pytest.ini` - конфигурация тестов
  - `requirements.txt` - зависимости Python
  - `.cursorrules` - правила для Cursor IDE

### 📁 Код и логика

- **`handlers_veretevo/`** - обработчики сообщений бота
- **`services_veretevo/`** - сервисы и бизнес-логика
- **`utils_veretevo/`** - утилиты и вспомогательные функции
  - `monitor_voice.py` - мониторинг голосовых сообщений
- **`config_veretevo/`** - конфигурация бота

### 📁 Тестирование

- **`tests/`** - все тестовые файлы
  - Тесты API и интеграции
  - Тесты обработки голосовых сообщений
  - Тесты GPT функционала
  - Тесты безопасности

### 📁 Скрипты и автоматизация

- **`scripts/`** - все скрипты и утилиты
  - `start-bot.sh` - запуск бота
  - `restart-bot.sh` - перезапуск бота
  - `check_status.sh` - проверка статуса
  - `run_tests.sh` - запуск тестов
  - Скрипты синхронизации и резервного копирования
  - Скрипты уведомлений и мониторинга

### 📁 Документация

- **`docs/`** - вся документация
  - `README.md` - основная документация
  - `FUNCTIONS_AVAILABLE.md` - доступные функции
  - `RESTART_INFO.md` - информация о перезапуске
  - Папки с руководствами и отчетами

### 📁 Данные и логи

- **`data/`** - данные бота
- **`logs/`** - логи работы
- **`backups/`** - резервные копии

## Запуск проекта

### Через systemd (рекомендуется)
```bash
sudo systemctl start veretevo-bot
sudo systemctl status veretevo-bot
```

### Ручной запуск
```bash
cd /home/ubuntu/bots/VeretevoTeam
python3 main.py
```

### Перезапуск
```bash
./scripts/restart-bot.sh
```

## Тестирование

```bash
./scripts/run_tests.sh
```

## Обновление systemd сервиса

После изменения структуры файлов обновите systemd сервис:

```bash
sudo cp config/veretevo-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable veretevo-bot
```
