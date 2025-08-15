# 📚 Индекс документации Veretevo Team Bot

## 📁 Структура документации

### 🚀 Руководства (`guides/`)
- **[QUICK_GUIDE.md](guides/QUICK_GUIDE.md)** - Единое руководство по разработке и управлению
- **[ENV_SETUP.md](guides/ENV_SETUP.md)** - Настройка переменных окружения
- **[CONTEXT_FOR_DEVELOPMENT.md](guides/CONTEXT_FOR_DEVELOPMENT.md)** - Чек-лист документов для разработки

### 📋 Стандарты (`standards/`)
- **[DEVELOPMENT_STANDARDS.md](standards/DEVELOPMENT_STANDARDS.md)** - Стандарты разработки
- **[task_buttons_algorithm.md](standards/task_buttons_algorithm.md)** - Алгоритм работы с кнопками задач

### 📖 Общая документация
- **[backup_guide.md](backup_guide.md)** - Руководство по резервному копированию

### 📊 Отчеты (`reports/`)
- **[README.md](reports/README.md)** - Индекс актуальных отчетов
- **[archive/](reports/archive/)** - Архив старых отчетов

### 📋 Общие отчеты
- **[GPT_ASSISTANTS_DISABLE_REPORT.md](GPT_ASSISTANTS_DISABLE_REPORT.md)** - Отключение GPT подсказок в чате Ассистентов

## 🎯 Быстрый доступ по ролям

### Для разработчиков:
1. **[DEVELOPMENT_STANDARDS.md](standards/DEVELOPMENT_STANDARDS.md)** - **ПОШАГОВЫЕ ИНСТРУКЦИИ** по внесению изменений в код
2. **[QUICK_GUIDE.md](guides/QUICK_GUIDE.md)** - быстрые команды и процессы
3. **[task_buttons_algorithm.md](standards/task_buttons_algorithm.md)** - логика кнопок

### Для администраторов:
1. **[ENV_SETUP.md](guides/ENV_SETUP.md)** - настройка окружения
2. **[QUICK_GUIDE.md](guides/QUICK_GUIDE.md)** - управление ботом
3. **[backup_guide.md](backup_guide.md)** - резервное копирование

### Для пользователей:
1. **[README.md](../README.md)** - основная документация проекта

## 📋 Чек-лист документов для разработки

### 🎯 Минимальный набор (обязательно)

**Основная документация:**
- `README.md` - общая структура проекта и возможности
- `docs/standards/DEVELOPMENT_STANDARDS.md` - стандарты разработки
- `docs/guides/QUICK_REFERENCE.md` - единое руководство по разработке и управлению

### 🔧 По типу функции

#### Для новых обработчиков Telegram
**Документы:**
- `handlers_veretevo/menu.py` - примеры обработчиков
- `handlers_veretevo/tasks.py` - логика работы с задачами
- `utils_veretevo/keyboards.py` - формирование клавиатур

**Примеры функций:**
- Новые команды бота
- Обработка новых типов сообщений
- Изменение логики меню

#### Для бизнес-логики
**Документы:**
- `services_veretevo/task_service.py` - работа с задачами
- `services_veretevo/department_service.py` - работа с отделами
- `config_veretevo/constants.py` - константы

**Примеры функций:**
- Новая логика обработки задач
- Изменения в работе с отделами
- Новые статусы задач

#### Для UI/интерфейса
**Документы:**
- `utils_veretevo/keyboards.py` - формирование клавиатур
- `utils_veretevo/formatting.py` - форматирование текста
- `utils_veretevo/media.py` - работа с медиа

**Примеры функций:**
- Новые кнопки и меню
- Изменение дизайна сообщений
- Добавление медиа-функций

#### Для новых отделов/ролей
**Документы:**
- `data/departments_config.json` - конфигурация отделов
- `services_veretevo/department_service.py` - логика отделов
- `config_veretevo/constants.py` - константы ролей

**Примеры функций:**
- Добавление нового отдела
- Изменение прав доступа
- Новая логика назначения

#### Для интеграций (Todoist, Yandex SpeechKit)
**Документы:**
- `utils_veretevo/todoist_sync_polling.py` - интеграция с Todoist
- `utils_veretevo/yandex_speechkit.py` - транскрипция
- `config_veretevo/env.py` - переменные окружения

**Примеры функций:**
- Новая интеграция с внешним сервисом
- Изменение логики синхронизации
- Добавление новых API

### 📊 Отчеты (для понимания истории)

#### Для задач и назначений
- `docs/reports/UNIFIED_TASK_ASSIGNMENT_REPORT.md`
- `docs/reports/ASSISTANT_TASK_FIX_REPORT.md`
- `docs/reports/GENERAL_DIRECTOR_ASSIGNMENT_REPORT.md`

#### Для проблем с отделами
- `docs/reports/DEPARTMENT_LOADING_FIX_REPORT.md`

#### Для изменений в документации
- `docs/reports/DOCUMENTATION_REORGANIZATION_REPORT.md`

## 🚀 Шаблоны запросов

### Быстрый старт
```
Приложенные документы:
- README.md
- docs/standards/DEVELOPMENT_STANDARDS.md
- docs/guides/QUICK_REFERENCE.md
- [соответствующий файл из handlers_veretevo/ или services_veretevo/]

Задача: [описание новой функции]
```

### Новая команда бота
```
Документы:
- handlers_veretevo/menu.py
- utils_veretevo/keyboards.py
- docs/standards/DEVELOPMENT_STANDARDS.md

Задача: Добавить команду /help с описанием всех функций
```

### Изменение логики задач
```
Документы:
- services_veretevo/task_service.py
- handlers_veretevo/tasks.py
- docs/reports/UNIFIED_TASK_ASSIGNMENT_REPORT.md

Задача: Добавить приоритеты для задач
```

### Новый отдел
```
Документы:
- data/departments_config.json
- services_veretevo/department_service.py
- docs/standards/DEVELOPMENT_STANDARDS.md

Задача: Добавить отдел "Маркетинг" с новыми правами
```

## ⚡ Советы по работе

1. **Всегда прикладывайте** `DEVELOPMENT_STANDARDS.md` - это сэкономит время на объяснениях
2. **Для UI-изменений** обязательно `keyboards.py` и `formatting.py`
3. **Для бизнес-логики** - соответствующие файлы из `services_veretevo/`
4. **Для новых функций** - похожие примеры из `handlers_veretevo/`

## 🔗 Связь с другими документами

- **[DEVELOPMENT_STANDARDS.md](standards/DEVELOPMENT_STANDARDS.md)** ← **ПЕРЕХОДИТЕ СЮДА** для пошаговых инструкций по внесению изменений
- **[QUICK_GUIDE.md](guides/QUICK_GUIDE.md)** ← быстрые команды и процессы управления
- **[task_buttons_algorithm.md](standards/task_buttons_algorithm.md)** ← логика работы с кнопками задач

## 📊 Статистика

- **Всего файлов документации:** 8 (сокращено с 23)
- **Руководств:** 3
- **Стандартов:** 2
- **Общих документов:** 1
- **Актуальных отчетов:** 2

## ✅ Преимущества структуры

1. **Нет дублирования** - каждая тема в одном месте
2. **Логичная структура** - от общего к частному
3. **Легко найти** - четкое назначение каждого файла
4. **Актуальность** - удалены устаревшие файлы
5. **Компактность** - сокращен объем на 65%

## 🔄 История изменений

### Объединено:
- `README.md` + `DOCUMENTATION.md` → единый `README.md`
- `QUICK_REFERENCE.md` + `QUICK_RESTART_GUIDE.md` → `QUICK_GUIDE.md`
- `INDEX.md` + `CONTEXT_FOR_DEVELOPMENT.md` → единый `INDEX.md`

### Архивировано:
- 13 старых отчетов → `reports/archive/`
- Оставлено 2 актуальных отчета

### Удалено:
- Дублирующие описания
- Устаревшие ссылки
- Неактуальная информация

---
*Обновлено: 28 июля 2025* 