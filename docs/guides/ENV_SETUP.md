# 🔧 Настройка переменных окружения

## 📋 Обзор

Проект использует переменные окружения для конфигурации. Все настройки хранятся в файле `.env` и загружаются через `config_veretevo.env`.

**Основные компоненты:**
- Telegram Bot API
- Yandex SpeechKit (транскрипция голосовых сообщений)
- Todoist API (синхронизация задач)

## 🔑 Yandex SpeechKit переменные

### Обязательные переменные:

```bash
# Yandex SpeechKit API ключ
YANDEX_SPEECHKIT_API_KEY=ваш_api_ключ_yandex_speechkit

# ID папки в Yandex Cloud
YANDEX_FOLDER_ID=ваш_folder_id_yandex_cloud
```

### Как получить:

1. **API ключ:** Создайте сервисный аккаунт в Yandex Cloud с ролью `ai.speechkit-stt.user`
2. **Folder ID:** Скопируйте ID папки из консоли Yandex Cloud

## 📁 Структура файлов

### `.env` файл (локальная разработка)
```bash
# Telegram Bot
TELEGRAM_TOKEN=ваш_токен_бота
ASSISTANTS_CHAT_ID=ваш_чат_id

# Yandex SpeechKit
YANDEX_SPEECHKIT_API_KEY=ваш_api_ключ
YANDEX_FOLDER_ID=ваш_folder_id
```

### Системные переменные (продакшн)
```bash
# Добавлены в /etc/environment
YANDEX_SPEECHKIT_API_KEY=ваш_api_ключ_yandex_speechkit
YANDEX_FOLDER_ID=ваш_folder_id_yandex_cloud
```

## 🔄 Приоритет загрузки

Модуль `YandexSpeechKitTranscriber` загружает переменные в следующем порядке:

1. **Параметры конструктора** (если переданы)
2. **config_veretevo.env** (основной источник)
3. **Системные переменные окружения** (fallback)

```python
self.api_key = api_key or env.YANDEX_SPEECHKIT_API_KEY or os.getenv('YANDEX_SPEECHKIT_API_KEY')
self.folder_id = folder_id or env.YANDEX_FOLDER_ID or os.getenv('YANDEX_FOLDER_ID')
```

## 🧪 Тестирование

### Проверка переменных:
```bash
python3 -c "from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber; t = YandexSpeechKitTranscriber(); print(f'API Key: {t.api_key[:10]}...'); print(f'Folder ID: {t.folder_id}')"
```

### Проверка подключения:
```bash
python3 test_yandex_speechkit.py
```

## 🚀 Развертывание

### Локальная разработка:
1. Скопируйте `.env.example` в `.env`
2. Заполните переменные своими значениями
3. Запустите бота: `python3 main.py`

### Продакшн сервер:
1. Добавьте переменные в `/etc/environment`
2. Перезапустите бота: `sudo systemctl restart veretevo-bot`
3. Проверьте статус: `sudo systemctl status veretevo-bot`

## 🔒 Безопасность

### ✅ Рекомендации:
- Не коммитьте `.env` файлы в git
- Используйте разные ключи для тестов и продакшна
- Регулярно ротируйте API ключи
- Ограничьте права сервисного аккаунта

### ❌ Не делайте:
- Не храните ключи в коде
- Не используйте один ключ для всех сред
- Не передавайте ключи через логи

## 📝 Примеры

### Полный .env файл:
```bash
# Telegram Bot Configuration
TELEGRAM_TOKEN=ваш_токен_бота
ASSISTANTS_CHAT_ID=ваш_чат_id

# Yandex SpeechKit (транскрипция голосовых сообщений)
YANDEX_SPEECHKIT_API_KEY=ваш_api_ключ_yandex_speechkit
YANDEX_FOLDER_ID=ваш_folder_id_yandex_cloud

# Todoist Integration (синхронизация задач)
TODOIST_API_TOKEN=ваш_токен_todoist
TODOIST_PROJECT_ID=ваш_project_id_todoist
```

### Проверка в коде:
```python
from config_veretevo import env

# Проверка наличия переменных
if env.YANDEX_SPEECHKIT_API_KEY:
    print("✅ API ключ установлен")
else:
    print("❌ API ключ не установлен")
```

---
**Последнее обновление:** 27 июля 2025  
**Статус:** ✅ Настроено и работает 