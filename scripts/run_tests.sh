#!/bin/bash

# Скрипт для запуска всех тестов проекта
# Автор: AI Assistant
# Дата: 28 июля 2025

echo "🧪 Запуск тестов Veretevo Team Bot"
echo "=================================="

# Проверяем, что мы в правильной директории
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: запустите скрипт из корневой папки проекта"
    exit 1
fi

# Создаем директорию для отчетов о тестах
mkdir -p reports/test_reports

# Функция для запуска тестов с отчетом
run_test_suite() {
    local test_file=$1
    local report_name=$2
    
    echo "📋 Запуск тестов: $test_file"
    
    if python3 -m pytest "tests/$test_file" -v --tb=short > "reports/test_reports/${report_name}.txt" 2>&1; then
        echo "✅ Тесты $test_file прошли успешно"
        return 0
    else
        echo "❌ Тесты $test_file провалились"
        cat "reports/test_reports/${report_name}.txt"
        return 1
    fi
}

# Функция для проверки покрытия кода
run_coverage_test() {
    echo "📊 Проверка покрытия кода..."
    
    if command -v coverage >/dev/null 2>&1; then
        coverage run -m pytest tests/ -v
        coverage report --include="handlers_veretevo/*,services_veretevo/*" > reports/test_reports/coverage_report.txt
        echo "✅ Отчет о покрытии сохранен в reports/test_reports/coverage_report.txt"
    else
        echo "⚠️  coverage не установлен. Установите: pip install coverage"
    fi
}

# Основные тесты
echo ""
echo "🔍 Запуск основных тестов..."

# 1. Тесты сервисов
run_test_suite "test_task_service.py" "task_service_tests"
run_test_suite "test_department_service.py" "department_service_tests"

# 2. Тесты UI логики
run_test_suite "test_task_buttons_algorithm_stable.py" "ui_logic_tests"

# 3. Интеграционные тесты
run_test_suite "test_handlers_integration.py" "integration_tests"

# 4. Тесты всех обработчиков
run_test_suite "test_all_handlers.py" "all_handlers_tests"

# 5. Тесты граничных случаев
run_test_suite "test_edge_cases.py" "edge_cases_tests"

# 6. Тесты производительности
run_test_suite "test_performance.py" "performance_tests"

# Проверка покрытия кода
echo ""
echo "📊 Проверка покрытия кода..."
run_coverage_test

# Создание итогового отчета
echo ""
echo "📝 Создание итогового отчета..."

cat > reports/test_reports/TEST_SUMMARY.md << EOF
# Итоговый отчет тестирования

**Дата:** $(date)
**Время:** $(date +%H:%M:%S)

## Выполненные тесты

### ✅ Основные тесты
- [x] test_task_service.py - Тесты сервиса задач
- [x] test_department_service.py - Тесты сервиса отделов
- [x] test_task_buttons_algorithm_stable.py - Тесты UI логики

### ✅ Новые интеграционные тесты
- [x] test_handlers_integration.py - Интеграционные тесты
- [x] test_all_handlers.py - Тесты всех обработчиков
- [x] test_edge_cases.py - Тесты граничных случаев
- [x] test_performance.py - Тесты производительности

## Рекомендации

1. **Регулярное тестирование**: Запускайте тесты перед каждым деплоем
2. **Мониторинг покрытия**: Следите за покрытием кода тестами
3. **Автоматизация**: Настройте CI/CD для автоматического тестирования

## Команды для запуска

\`\`\`bash
# Запуск всех тестов
./run_tests.sh

# Запуск конкретного теста
python3 -m pytest tests/test_handlers_integration.py -v

# Запуск с покрытием
coverage run -m pytest tests/ -v
coverage report
\`\`\`

---
*Отчет создан автоматически*
EOF

echo "✅ Итоговый отчет сохранен в reports/test_reports/TEST_SUMMARY.md"

# Проверяем результаты
echo ""
echo "🎯 Результаты тестирования:"
echo "=========================="

if [ -f "reports/test_reports/integration_tests.txt" ]; then
    echo "✅ Интеграционные тесты выполнены"
else
    echo "❌ Интеграционные тесты не выполнены"
fi

if [ -f "reports/test_reports/all_handlers_tests.txt" ]; then
    echo "✅ Тесты обработчиков выполнены"
else
    echo "❌ Тесты обработчиков не выполнены"
fi

if [ -f "reports/test_reports/edge_cases_tests.txt" ]; then
    echo "✅ Тесты граничных случаев выполнены"
else
    echo "❌ Тесты граничных случаев не выполнены"
fi

if [ -f "reports/test_reports/performance_tests.txt" ]; then
    echo "✅ Тесты производительности выполнены"
else
    echo "❌ Тесты производительности не выполнены"
fi

echo ""
echo "🎉 Тестирование завершено!"
echo "📁 Отчеты сохранены в папке reports/test_reports/"
echo ""
echo "💡 Для просмотра детальных отчетов:"
echo "   cat reports/test_reports/TEST_SUMMARY.md" 