from utils_veretevo.todoist_service import get_director_tasks_from_todoist
from services_veretevo.task_service import add_or_update_task
from config_veretevo.env import ASSISTANTS_CHAT_ID
import datetime
import logging

# Пример функции синхронизации

def sync_todoist_to_bot(tasks, GENERAL_DIRECTOR_ID, application=None):
    print("Запуск sync_todoist_to_bot")
    try:
        todoist_tasks = get_director_tasks_from_todoist()
        print(f"Получено {len(todoist_tasks)} задач из Todoist")
        todoist_map = {str(t['id']): t for t in todoist_tasks}
        # Индексируем задачи бота по todoist_task_id
        bot_todoist_ids = {str(task.get('todoist_task_id')): task for task in tasks if task.get('todoist_task_id')}
        print(f"Найдено {len(bot_todoist_ids)} задач бота с todoist_task_id")
    except Exception as e:
        print(f"Ошибка при получении задач из Todoist: {e}")
        return
    # 1. Обновляем существующие задачи
    updated_tasks = []
    for task in tasks:
        if task.get('assistant_id') == GENERAL_DIRECTOR_ID and task.get('todoist_task_id'):
            tid = str(task['todoist_task_id'])
            if tid in todoist_map:
                todoist_task = todoist_map[tid]
                new_status = 'завершено' if todoist_task['status'] == 'завершено' else 'в работе'
                old_status = task.get('status')
                task['status'] = new_status
                if 'todoist_comments' not in task:
                    task['todoist_comments'] = []
                existing = {c['id'] for c in task['todoist_comments']}
                for comment in todoist_task['comments']:
                    if comment['id'] not in existing:
                        print(f"Добавляю комментарий из Todoist в задачу {task['id']}")
                        task['todoist_comments'].append(comment)
                add_or_update_task(task)
                # Если статус изменился, добавляем задачу в список для обновления сообщений
                if old_status != new_status:
                    updated_tasks.append(task)
            else:
                # Если задача есть в боте, но её нет в Todoist — помечаем как отменённую
                if task.get('status') != 'отменено':
                    print(f"Задача {task['id']} отсутствует в Todoist, помечаю как отменённую.")
                    task['status'] = 'отменено'
                    task.setdefault('history', []).append({'action': 'cancel_by_todoist', 'by': 'todoist'})
                    add_or_update_task(task)
                    updated_tasks.append(task)
    # 2. Добавляем новые задачи из Todoist, которых нет в боте
    for tid, todoist_task in todoist_map.items():
        if tid not in bot_todoist_ids:
            # Создаём новую задачу в боте
            new_task = {
                'id': int(str(todoist_task['id'])[-9:]),  # генерируем уникальный id на основе todoist_id
                'text': f"[TODOIST] {todoist_task.get('content', 'Без названия')}",
                'status': todoist_task['status'],
                'author_id': GENERAL_DIRECTOR_ID,
                'author_name': 'Генеральный директор',
                'assistant_id': GENERAL_DIRECTOR_ID,
                'assistant_name': 'Генеральный директор',
                'department': None,
                'department_member': None,
                'created_at': datetime.datetime.now().isoformat(),
                'chat_id': 0,
                'history': [{'action': 'imported_from_todoist', 'by': GENERAL_DIRECTOR_ID}],
                'todoist_task_id': todoist_task['id'],
                'todoist_comments': todoist_task.get('comments', []),
            }
            print(f"Создаю новую задачу из Todoist: {new_task['text']}")
            add_or_update_task(new_task)
    print('tasks.json обновлён по данным из Todoist.')
    
    # 3. Обновляем сообщения в Telegram для изменившихся задач
    if updated_tasks:
        print(f"Найдено {len(updated_tasks)} задач для обновления сообщений")
        print(f"Application передан: {application is not None}")
        update_telegram_messages(updated_tasks, application)
    else:
        print("Нет задач для обновления сообщений")

def update_telegram_messages(tasks, application=None):
    """
    Обновляет сообщения в Telegram для задач, статус которых изменился
    """
    from telegram import InlineKeyboardMarkup
    from utils_veretevo.keyboards import get_task_action_keyboard
    from utils_veretevo.media import send_task_with_media
    import asyncio
    
    print(f"Запуск update_telegram_messages для {len(tasks)} задач")
    
    async def update_messages_async():
        # Получаем application через глобальную переменную, если не передан
        current_application = application
        if current_application is None:
            import main
            current_application = main.application
        
        for task in tasks:
            try:
                # Получаем новую клавиатуру (пустую для завершённых/отменённых задач)
                keyboard = get_task_action_keyboard(task, None)
                
                # Обновляем сообщения в группах
                if task.get('group_messages'):
                    for msg_info in task['group_messages']:
                        try:
                            await current_application.bot.edit_message_text(
                                chat_id=msg_info['chat_id'],
                                message_id=msg_info['message_id'],
                                text=format_task_text(task),
                                reply_markup=keyboard,
                                parse_mode='HTML'
                            )
                            logging.info(f"Обновлено групповое сообщение для задачи {task['id']} в чате {msg_info['chat_id']}")
                        except Exception as e:
                            logging.error(f"Ошибка обновления группового сообщения: {e}")
                
                # Обновляем сообщения в личных чатах
                if task.get('private_messages'):
                    for msg_info in task['private_messages']:
                        try:
                            await current_application.bot.edit_message_text(
                                chat_id=msg_info['chat_id'],
                                message_id=msg_info['message_id'],
                                text=format_task_text(task),
                                reply_markup=keyboard,
                                parse_mode='HTML'
                            )
                            logging.info(f"Обновлено личное сообщение для задачи {task['id']} в чате {msg_info['chat_id']}")
                        except Exception as e:
                            logging.error(f"Ошибка обновления личного сообщения: {e}")
                
                # Обновляем сообщение в чате ассистентов
                if task.get('assistant_message_id'):
                    try:
                        await current_application.bot.edit_message_text(
                            chat_id=ASSISTANTS_CHAT_ID,
                            message_id=task['assistant_message_id'],
                            text=format_task_text(task),
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                        logging.info(f"Обновлено сообщение ассистентов для задачи {task['id']}")
                    except Exception as e:
                        logging.error(f"Ошибка обновления сообщения ассистентов: {e}")
                
                # Обновляем сообщение в чате отдела
                if task.get('department_message_id'):
                    try:
                        await current_application.bot.edit_message_text(
                            chat_id=task.get('chat_id'),
                            message_id=task['department_message_id'],
                            text=format_task_text(task),
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                        logging.info(f"Обновлено сообщение отдела для задачи {task['id']}")
                    except Exception as e:
                        logging.error(f"Ошибка обновления сообщения отдела: {e}")
                        
            except Exception as e:
                logging.error(f"Ошибка обновления сообщений для задачи {task['id']}: {e}")
    
    # Запускаем асинхронную функцию
    try:
        # Проверяем, есть ли уже запущенный цикл событий
        try:
            loop = asyncio.get_running_loop()
            # Если цикл уже запущен, создаём задачу
            asyncio.create_task(update_messages_async())
        except RuntimeError:
            # Если нет запущенного цикла, создаём новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(update_messages_async())
            loop.close()
    except Exception as e:
        logging.error(f"Ошибка запуска обновления сообщений: {e}")
        print(f"Ошибка запуска обновления сообщений: {e}")

def format_task_text(task):
    """
    Форматирует текст задачи для отображения в Telegram
    """
    # Используем основную функцию форматирования
    from utils_veretevo.formatting import format_task_message
    return format_task_message(task)

def force_update_task_messages(task_id, application):
    """
    Принудительно обновляет сообщения для конкретной задачи
    """
    import json
    from services_veretevo.task_service import get_tasks
    
    print(f"force_update_task_messages вызвана для задачи {task_id}")
    
    try:
        tasks = get_tasks()
        print(f"Загружено {len(tasks)} задач")
        task = None
        for t in tasks:
            if t.get('id') == task_id:
                task = t
                break
        
        if task:
            print(f"Найдена задача {task_id}: {task.get('text', 'Без названия')}")
            print(f"Статус задачи: {task.get('status')}")
            print(f"Есть group_messages: {bool(task.get('group_messages'))}")
            print(f"Есть private_messages: {bool(task.get('private_messages'))}")
            update_telegram_messages([task], application)
        else:
            print(f"Задача {task_id} не найдена")
    except Exception as e:
        print(f"Ошибка при обновлении сообщений для задачи {task_id}: {e}")
        import traceback
        traceback.print_exc() 