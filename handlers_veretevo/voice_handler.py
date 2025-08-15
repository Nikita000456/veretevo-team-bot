"""
Универсальный обработчик голосовых сообщений для всех групп.
Обеспечивает транскрипцию голосовых сообщений в любом чате.
"""
import logging
import tempfile
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from utils_veretevo.yandex_speechkit import YandexSpeechKitTranscriber
from utils_veretevo.yandex_gpt import improve_task_text
from services_veretevo.department_service import DEPARTMENTS, load_departments
import re

# Инициализируем Yandex SpeechKit транскрайбер
try:
    voice_transcriber = YandexSpeechKitTranscriber()
    logging.info("[INFO] Yandex SpeechKit транскрайбер инициализирован успешно")
except Exception as e:
    logging.error(f"[ОШИБКА] Не удалось инициализировать Yandex SpeechKit: {e}")
    voice_transcriber = None

async def handle_voice_message_universal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Универсальный обработчик голосовых сообщений для всех чатов.
    Транскрибирует голосовые сообщения и показывает результат.
    """
    if not update.message.voice:
        return
    
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user = update.effective_user
    
    logging.info(f"[VOICE] Получено голосовое сообщение в чате {chat_id} ({chat_type}) от пользователя {user.id if user else 'Unknown'}")
    
    # Скачиваем файл
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
            await file.download_to_drive(temp_audio.name)
            logging.info(f"[VOICE] Аудиофайл сохранен: {temp_audio.name}")
            
            # Транскрибируем
            transcript = None
            if voice_transcriber:
                try:
                    transcript = voice_transcriber.process_audio_file(temp_audio.name)
                    logging.info(f"[VOICE] Транскрипция успешна: '{transcript}'")
                except Exception as e:
                    logging.error(f"[ОШИБКА] Ошибка при транскрипции: {e}")
                    transcript = None
            else:
                logging.error(f"[VOICE] voice_transcriber равен None!")
                await update.message.reply_text("⚠️ Служба распознавания речи недоступна.")
                return
            
            # Удаляем временный файл
            os.unlink(temp_audio.name)
            
            if transcript and transcript.strip():
                # Улучшаем текст через Yandex GPT
                try:
                    improved = improve_task_text(transcript)
                    logging.info(f"[VOICE] Улучшенный текст: '{improved}'")
                except Exception as e:
                    logging.error(f"[ОШИБКА] Ошибка улучшения текста: {e}")
                    improved = transcript
                
                # Определяем отдел по тексту
                dep_key = extract_department_from_text(improved)
                dep_name = None
                if dep_key and dep_key in DEPARTMENTS:
                    dep_name = DEPARTMENTS[dep_key]['name']
                    logging.info(f"[VOICE] Найден отдел: {dep_name}")
                
                # Формируем ответ
                response_text = f"🎤 **Распознанный текст:**\n\n{improved}"
                
                if dep_name:
                    response_text += f"\n\n🏢 **Обнаружен отдел:** {dep_name}"
                    
                    # В личных чатах предлагаем создать задачу
                    if chat_type == "private":
                        keyboard = [[InlineKeyboardButton("📌 Создать задачу", callback_data=f"create_task_from_voice_{dep_key}")]]
                        await update.message.reply_text(
                            response_text + "\n\nХотите создать задачу?",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode="Markdown"
                        )
                    else:
                        # В группах просто показываем транскрипцию
                        await update.message.reply_text(
                            response_text,
                            parse_mode="Markdown"
                        )
                else:
                    # Отдел не определен
                    await update.message.reply_text(
                        response_text,
                        parse_mode="Markdown"
                    )
            else:
                await update.message.reply_text("❌ Не удалось распознать речь в голосовом сообщении.")
                
    except Exception as e:
        logging.error(f"[ОШИБКА] Ошибка обработки голосового сообщения: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")

def extract_department_from_text(text: str) -> str:
    """
    Пытается найти отдел по ключевым словам в тексте.
    Возвращает ключ отдела или None.
    """
    if not text:
        return None
        
    text = text.lower()
    
    # Словарь сокращений и альтернативных названий для всех возможных отделов
    # Приоритет: более специфичные ключевые слова идут первыми
    dep_map = {
        'assistants': ['ассистенты', 'ассистент', 'ассист', 'помощник', 'помощники', 'помощь', 'помогите'],
        'carpenters': ['плотники', 'плотник', 'плотницкие', 'плотницкая'],
        'maintenance': ['эксплуатация', 'эксплуат', 'техэксплуатация', 'техобслуживание', 'обслуживание'],
        'tech': ['тех команда', 'техкоманда', 'тех', 'технический', 'техники', 'техник'],
        'maids': ['горничные', 'горничная', 'уборка', 'уборщицы', 'уборщица', 'клининг'],
        'reception': ['ресепшен', 'ресеп', 'приём', 'прием', 'администрация', 'админ'],
        'security': ['охрана', 'охранник', 'безопасность', 'секьюрити', 'сторож'],
        'finance': ['финансы', 'финанс', 'бухгалтерия', 'бухгалтер', 'касса', 'деньги', 'оплата'],
        # Новые группы из shared
        'construction': ['стройка', 'строительный', 'строители', 'строительство', 'постройка', 'вопрос по стройке'],
        'management': ['руководители', 'руководство', 'менеджмент', 'управление', 'директор'],
        'info': ['инфо', 'информация', 'уведомления', 'брифинги'],
        # Добавляем поддержку для возможных будущих отделов
        'kitchen': ['кухня', 'повар', 'повара', 'кулинария', 'готовка'],
        'housekeeping': ['хозяйство', 'хозяйственный', 'хозяйственные'],
        'engineering': ['инженерия', 'инженер', 'инженеры', 'технический'],
        'sales': ['продажи', 'продавец', 'продавцы', 'коммерция'],
        'marketing': ['маркетинг', 'реклама', 'продвижение'],
        'hr': ['hr', 'hr-отдел', 'кадры', 'персонал', 'человеческие ресурсы'],
        'legal': ['юридический', 'юрист', 'юристы', 'правовой'],
        'it': ['it', 'айти', 'информационные технологии', 'программисты'],
    }
    
    # Ищем фразы "отдел ...", "в отдел ...", "вопрос по ...", "проблема с ..."
    match = re.search(r'(?:отдел|в отдел|вопрос по|проблема с|нужна|нужен)\s+([\w\-]+)', text)
    if match:
        word = match.group(1)
        for dep_key, variants in dep_map.items():
            if word in variants or word in dep_key or word in DEPARTMENTS.get(dep_key, {}).get('name', '').lower():
                return dep_key
    
    # Ищем по специфичным ключевым словам (более точное определение)
    specific_keywords = {
        'assistants': ['помогите', 'консультация'],
        'carpenters': ['плотник', 'дерево', 'мебель'],
        'maintenance': ['эксплуатация', 'техобслуживание'],
        'tech': ['тех команда', 'техкоманда'],
        'maids': ['горничная', 'клининг'],
        'reception': ['ресепшен', 'регистрация', 'гость'],
        'security': ['охрана', 'охранник', 'сторож'],
        'finance': ['финансы', 'бухгалтерия', 'касса'],
        'construction': ['стройка', 'строители', 'строительство', 'строительный'],
        'management': ['руководители', 'менеджмент', 'управление'],
        'info': ['инфо', 'уведомления', 'брифинги'],
        'kitchen': ['кухня', 'повар', 'кулинария'],
        'housekeeping': ['хозяйство', 'инвентарь'],
        'engineering': ['инженерия', 'инженер'],
        'sales': ['продажи', 'продавец'],
        'marketing': ['маркетинг', 'реклама'],
        'hr': ['hr-отдел', 'кадры', 'персонал'],
        'legal': ['юридический', 'юрист'],
        'it': ['it', 'айти', 'программисты'],
    }
    
    # Сначала ищем по специфичным ключевым словам
    for dep_key, keywords in specific_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return dep_key
    
    # Затем ищем по общим ключевым словам (менее приоритетно)
    general_keywords = {
        'assistants': ['помощь', 'помощник'],
        'carpenters': ['ремонт', 'постройка'],
        'maintenance': ['обслуживание', 'техника', 'оборудование'],
        'tech': ['тех', 'технический', 'техники'],
        'maids': ['уборщицы', 'чистота', 'постель', 'белье'],
        'reception': ['администрация', 'админ', 'номер', 'бронирование'],
        'security': ['безопасность', 'секьюрити', 'пропуск', 'контроль', 'досмотр'],
        'finance': ['финанс', 'деньги', 'оплата', 'счет'],
        'construction': ['строительство', 'постройка', 'ремонт'],
        'management': ['руководство', 'директор', 'начальник'],
        'info': ['информация', 'новости', 'объявления'],
        'kitchen': ['еда', 'готовка', 'рецепт'],
        'housekeeping': ['хозяйственный', 'снабжение'],
        'engineering': ['проект', 'чертеж', 'конструкция'],
        'sales': ['клиент', 'заказ', 'договор', 'сделка'],
        'marketing': ['продвижение', 'бренд'],
        'hr': ['отпуск', 'больничный', 'увольнение'],
        'legal': ['документ', 'договор', 'соглашение', 'закон'],
        'it': ['компьютер', 'программа', 'система', 'база данных'],
    }
    
    # Ищем по общим ключевым словам, но исключаем слишком общие
    for dep_key, keywords in general_keywords.items():
        for keyword in keywords:
            if keyword in text:
                # Исключаем слишком общие слова для assistants
                if dep_key == 'assistants' and keyword in ['помощь', 'помощник']:
                    # Проверяем, нет ли более специфичных указаний на другие отделы
                    if any(other_keyword in text for other_keyword in ['плотник', 'горничная', 'ресепшен', 'охрана', 'финансы', 'кухня', 'инженер', 'стройка', 'руководители']):
                        continue
                return dep_key
    
    return None

def register_voice_handlers(application):
    """
    Регистрирует обработчики голосовых сообщений для всех чатов.
    """
    # Загружаем актуальные отделы
    load_departments()
    
    # Регистрируем универсальный обработчик голосовых сообщений
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message_universal))
    
    logging.info("✅ Обработчики голосовых сообщений зарегистрированы для всех чатов")
    
    # Логируем информацию о доступных группах
    active_groups = [k for k, v in DEPARTMENTS.items() if v.get('chat_id')]
    inactive_groups = [k for k, v in DEPARTMENTS.items() if not v.get('chat_id')]
    
    logging.info(f"[VOICE] Активные группы с чатами: {active_groups}")
    if inactive_groups:
        logging.info(f"[VOICE] Группы без настроенных чатов (транскрипция будет работать при добавлении): {inactive_groups}")
