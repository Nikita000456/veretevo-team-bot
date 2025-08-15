import os

# Проверка размера файлов в handlers
handlers_dir = os.path.join(os.path.dirname(__file__), '../handlers_veretevo')
max_lines = 500
problems = []
for fname in os.listdir(handlers_dir):
    if fname.endswith('.py'):
        path = os.path.join(handlers_dir, fname)
        with open(path) as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                problems.append(f"Файл {fname} в handlers_veretevo слишком большой: {len(lines)} строк")

# Проверка utils
utils_dir = os.path.join(os.path.dirname(__file__), '../utils_veretevo')
for fname in os.listdir(utils_dir):
    if fname.endswith('.py') and 'util' not in fname and 'service' not in fname and 'media' not in fname:
        problems.append(f"В utils_veretevo подозрительный файл: {fname}")

# Документация
docs_dir = os.path.join(os.path.dirname(__file__), '../docs')
if not os.path.exists(os.path.join(docs_dir, 'task_buttons_algorithm.md')):
    problems.append("Нет task_buttons_algorithm.md в docs/")

# Тесты
tests_dir = os.path.join(os.path.dirname(__file__), '../tests')
if not any(f.endswith('.py') for f in os.listdir(tests_dir)):
    problems.append("Нет тестов в tests/")

if problems:
    print("Проблемы со структурой проекта:")
    for p in problems:
        print("-", p)
else:
    print("Структура проекта в порядке!") 