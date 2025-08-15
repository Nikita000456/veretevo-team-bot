#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчики команд по управлению контактами
Доступ только для отделов: Ассистенты, Руководители, Стройка
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, Application, ConversationHandler
from telegram.constants import ParseMode

# Импортируем клавиатуры
from utils_veretevo.keyboards import (
    contacts_menu_keyboard, 
    contact_categories_keyboard, 
    contact_actions_keyboard,
    contact_creation_keyboard,
    main_menu_keyboard
)

# Импортируем сервис отделов
from services_veretevo.department_service import DEPARTMENTS

# Импортируем knowledge_collector для работы с контактами
import sys
sys.path.append('/home/ubuntu/bots/shared')
from ai_service.knowledge_collector import KnowledgeCollector

logger = logging.getLogger(__name__)

# Разрешенные отделы для работы с контактами
ALLOWED_DEPARTMENTS = ['Ассистенты', 'Руководители', 'Стройка']

# ID чата "Веретево Инфо" для уведомлений
VERETEVO_INFO_CHAT_ID = None  # Нужно будет получить реальный ID

# Состояния для ConversationHandler
(
    CONTACTS_MENU,
    ADDING_CONTACT_NAME,
    ADDING_CONTACT_PHONE,
    ADDING_CONTACT_EMAIL,
    ADDING_CONTACT_ADDRESS,
    ADDING_CONTACT_WEBSITE,
    ADDING_CONTACT_DESCRIPTION,
    ADDING_CONTACT_CATEGORY,
    EDITING_CONTACT,
    SEARCHING_CONTACT
) = range(10)

class ContactsHandler:
    """Обработчик команд по контактам"""
    
    def __init__(self):
        self.knowledge_collector = KnowledgeCollector()
        self.veretevo_info_chat_id = self._get_veretevo_info_chat_id()
    
    def _get_veretevo_info_chat_id(self) -> Optional[int]:
        """Получение ID чата Веретево Инфо"""
        try:
            # Здесь должна быть логика получения ID чата
            # Пока используем заглушку
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения ID чата Веретево Инфо: {e}")
            return None
    
    def _check_user_access(self, user_id: int) -> bool:
        """Проверка доступа пользователя к функциям контактов"""
        try:
            if not user_id:
                return False
            
            # Проверяем, в каких отделах состоит пользователь
            user_departments = []
            for dept_name, dept_data in DEPARTMENTS.items():
                if str(user_id) in dept_data.get('members', []):
                    user_departments.append(dept_name)
            
            # Проверяем, есть ли пересечение с разрешенными отделами
            for dept in user_departments:
                if dept in ALLOWED_DEPARTMENTS:
                    return True
            
            logger.info(f"🚫 Пользователь {user_id} не имеет доступа к контактам. Отделы: {user_departments}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа пользователя {user_id}: {e}")
            return False
    
    async def _send_notification_to_veretevo_info(self, message: str, context: ContextTypes.DEFAULT_TYPE):
        """Отправка уведомления в чат Веретево Инфо"""
        try:
            if not self.veretevo_info_chat_id:
                logger.warning("⚠️ ID чата Веретево Инфо не найден, уведомление не отправлено")
                return
            
            await context.bot.send_message(
                chat_id=self.veretevo_info_chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"✅ Уведомление отправлено в Веретево Инфо: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления в Веретево Инфо: {e}")
    
    async def contacts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /contacts"""
        try:
            user_id = update.effective_user.id
            chat_type = update.effective_chat.type
            
            # Проверяем, что это личный чат
            if chat_type != "private":
                await update.message.reply_text(
                    "❌ Команды по контактам доступны только в личном чате с ботом!",
                    reply_markup=main_menu_keyboard("private", user_id)
                )
                return
            
            # Проверяем права доступа
            if not self._check_user_access(user_id):
                await update.message.reply_text(
                    "🚫 У вас нет доступа к управлению контактами.\n"
                    "Доступ разрешен только для отделов: Ассистенты, Руководители, Стройка.",
                    reply_markup=main_menu_keyboard("private", user_id)
                )
                return
            
            # Показываем меню контактов
            await update.message.reply_text(
                "📞 <b>УПРАВЛЕНИЕ КОНТАКТАМИ</b>\n\n"
                "Выберите действие:",
                reply_markup=contacts_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка команды /contacts: {e}")
            await update.message.reply_text("❌ Произошла ошибка при открытии меню контактов")
    
    async def contacts_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик нажатия кнопки '📞 Контакты'"""
        try:
            user_id = update.effective_user.id
            chat_type = update.effective_chat.type
            
            # Проверяем, что это личный чат
            if chat_type != "private":
                await update.message.reply_text(
                    "❌ Функции контактов доступны только в личном чате с ботом!"
                )
                return
            
            # Проверяем права доступа
            if not self._check_user_access(user_id):
                await update.message.reply_text(
                    "🚫 У вас нет доступа к управлению контактами.\n"
                    "Доступ разрешен только для отделов: Ассистенты, Руководители, Стройка."
                )
                return
            
            # Показываем меню контактов
            await update.message.reply_text(
                "📞 <b>УПРАВЛЕНИЕ КОНТАКТАМИ</b>\n\n"
                "Выберите действие:",
                reply_markup=contacts_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки кнопки контактов: {e}")
            await update.message.reply_text("❌ Произошла ошибка при открытии меню контактов")
    
    async def contacts_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback-запросов от inline-кнопок"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            callback_data = query.data
            
            # Проверяем права доступа
            if not self._check_user_access(user_id):
                await query.edit_message_text(
                    "🚫 У вас нет доступа к управлению контактами.\n"
                    "Доступ разрешен только для отделов: Ассистенты, Руководители, Стройка."
                )
                return
            
            # Обрабатываем различные callback'и
            if callback_data == "contacts_find":
                await self._handle_find_contact(query, context)
            elif callback_data == "contacts_add":
                await self._handle_add_contact(query, context)
            elif callback_data == "contacts_list":
                await self._handle_list_contacts(query, context)
            elif callback_data == "contacts_categories":
                await self._handle_show_categories(query, context)
            elif callback_data == "contacts_export":
                await self._handle_export_contacts(query, context)
            elif callback_data == "contacts_main_menu":
                await self._handle_main_menu(query, context)
            elif callback_data.startswith("category_"):
                await self._handle_category_selection(query, context, callback_data)
            else:
                await query.edit_message_text("❌ Неизвестная команда")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")
            try:
                await query.edit_message_text("❌ Произошла ошибка при обработке команды")
            except:
                pass
    
    async def _handle_find_contact(self, query, context):
        """Обработка поиска контакта"""
        await query.edit_message_text(
            "🔍 <b>ПОИСК КОНТАКТА</b>\n\n"
            "Введите имя, телефон или описание для поиска:",
            parse_mode=ParseMode.HTML
        )
        
        # Переходим к состоянию поиска
        return SEARCHING_CONTACT
    
    async def _handle_add_contact(self, query, context):
        """Обработка добавления контакта"""
        # Устанавливаем состояние добавления контакта
        context.user_data['contact_creation'] = {
            'name': '',
            'phone': '',
            'email': '',
            'address': '',
            'website': '',
            'description': '',
            'category': 'supplier'
        }
        
        await query.edit_message_text(
            "➕ <b>ДОБАВЛЕНИЕ КОНТАКТА</b>\n\n"
            "Введите название компании или имя контакта:",
            parse_mode=ParseMode.HTML
        )
        
        # Переходим к состоянию ввода имени
        return ADDING_CONTACT_NAME
    
    async def _handle_list_contacts(self, query, context):
        """Обработка списка всех контактов"""
        try:
            # Получаем все контакты
            all_contacts = []
            for phone, data in self.knowledge_collector.suppliers_database.items():
                all_contacts.append({
                    'phone': phone,
                    'name': data.get('name', 'Unknown'),
                    'category': data.get('category', 'supplier'),
                    'email': data.get('email', ''),
                    'internet_enriched': data.get('internet_enriched', 'false')
                })
            
            if not all_contacts:
                await query.edit_message_text(
                    "📋 <b>СПИСОК КОНТАКТОВ</b>\n\n"
                    "ℹ️ В базе пока нет контактов.\n"
                    "Добавьте первый контакт!",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Формируем список контактов
            contacts_text = "📋 <b>СПИСОК КОНТАКТОВ</b>\n\n"
            for i, contact in enumerate(all_contacts[:20], 1):  # Показываем первые 20
                enriched_icon = "🌐" if contact['internet_enriched'] == 'true' else "📞"
                contacts_text += f"{i}. {enriched_icon} <b>{contact['name']}</b>\n"
                contacts_text += f"   📱 {contact['phone']}\n"
                contacts_text += f"   🏷️ {contact['category']}\n"
                if contact['email']:
                    contacts_text += f"   📧 {contact['email']}\n"
                contacts_text += "\n"
            
            if len(all_contacts) > 20:
                contacts_text += f"... и еще {len(all_contacts) - 20} контактов\n\n"
            
            contacts_text += "Используйте кнопки ниже для управления:"
            
            await query.edit_message_text(
                contacts_text,
                reply_markup=contacts_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка контактов: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка контактов")
    
    async def _handle_show_categories(self, query, context):
        """Показ категорий контактов"""
        await query.edit_message_text(
            "🏷️ <b>КАТЕГОРИИ КОНТАКТОВ</b>\n\n"
            "Выберите категорию для просмотра:",
            reply_markup=contact_categories_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_export_contacts(self, query, context):
        """Экспорт контактов"""
        try:
            # Получаем все контакты
            all_contacts = []
            for phone, data in self.knowledge_collector.suppliers_database.items():
                all_contacts.append({
                    'phone': phone,
                    'name': data.get('name', 'Unknown'),
                    'email': data.get('email', ''),
                    'address': data.get('address', ''),
                    'website': data.get('website', ''),
                    'description': data.get('description', ''),
                    'category': data.get('category', 'supplier'),
                    'tags': data.get('tags', []),
                    'first_added': data.get('first_added', ''),
                    'last_updated': data.get('last_updated', ''),
                    'internet_enriched': data.get('internet_enriched', 'false')
                })
            
            if not all_contacts:
                await query.edit_message_text(
                    "📤 <b>ЭКСПОРТ КОНТАКТОВ</b>\n\n"
                    "ℹ️ В базе нет контактов для экспорта.",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Формируем экспорт в текстовом формате
            export_text = "📤 <b>ЭКСПОРТ КОНТАКТОВ</b>\n\n"
            export_text += f"Всего контактов: {len(all_contacts)}\n"
            export_text += f"Дата экспорта: {context.bot.get_me().first_name}\n\n"
            
            for contact in all_contacts:
                export_text += f"🏢 <b>{contact['name']}</b>\n"
                export_text += f"📱 Телефон: {contact['phone']}\n"
                if contact['email']:
                    export_text += f"📧 Email: {contact['email']}\n"
                if contact['address']:
                    export_text += f"🏠 Адрес: {contact['address']}\n"
                if contact['website']:
                    export_text += f"🌐 Сайт: {contact['website']}\n"
                if contact['description']:
                    export_text += f"📝 Описание: {contact['description']}\n"
                export_text += f"🏷️ Категория: {contact['category']}\n"
                export_text += f"🌐 Обогащен: {'Да' if contact['internet_enriched'] == 'true' else 'Нет'}\n"
                export_text += "─" * 30 + "\n\n"
            
            # Разбиваем на части, если текст слишком длинный
            if len(export_text) > 4000:
                parts = [export_text[i:i+4000] for i in range(0, len(export_text), 4000)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await query.edit_message_text(part, parse_mode=ParseMode.HTML)
                    else:
                        await context.bot.send_message(
                            chat_id=query.from_user.id,
                            text=part,
                            parse_mode=ParseMode.HTML
                        )
            else:
                await query.edit_message_text(
                    export_text,
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта контактов: {e}")
            await query.edit_message_text("❌ Ошибка при экспорте контактов")
    
    async def _handle_main_menu(self, query, context):
        """Возврат в главное меню"""
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=main_menu_keyboard("private", query.from_user.id)
        )
    
    async def _handle_category_selection(self, query, context, callback_data):
        """Обработка выбора категории"""
        try:
            category = callback_data.replace("category_", "")
            category_names = {
                'supplier': 'Поставщики',
                'contractor': 'Подрядчики', 
                'employee': 'Сотрудники'
            }
            
            # Получаем контакты по категории
            contacts = self.knowledge_collector.get_contacts_by_category(category)
            
            if not contacts:
                await query.edit_message_text(
                    f"🏷️ <b>КАТЕГОРИЯ: {category_names.get(category, category)}</b>\n\n"
                    f"ℹ️ В этой категории пока нет контактов.",
                    reply_markup=contact_categories_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Формируем список контактов по категории
            contacts_text = f"🏷️ <b>КАТЕГОРИЯ: {category_names.get(category, category)}</b>\n\n"
            contacts_text += f"Найдено контактов: {len(contacts)}\n\n"
            
            for i, contact in enumerate(contacts[:15], 1):  # Показываем первые 15
                enriched_icon = "🌐" if contact['internet_enriched'] == 'true' else "📞"
                contacts_text += f"{i}. {enriched_icon} <b>{contact['name']}</b>\n"
                contacts_text += f"   📱 {contact['phone']}\n"
                if contact['email']:
                    contacts_text += f"   📧 {contact['email']}\n"
                contacts_text += "\n"
            
            if len(contacts) > 15:
                contacts_text += f"... и еще {len(contacts) - 15} контактов\n\n"
            
            await query.edit_message_text(
                contacts_text,
                reply_markup=contact_categories_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контактов по категории: {e}")
            await query.edit_message_text("❌ Ошибка при получении контактов по категории")

    # Методы для работы с состояниями добавления контакта
    async def handle_contact_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода имени контакта"""
        try:
            name = update.message.text.strip()
            if not name or len(name) < 2:
                await update.message.reply_text(
                    "❌ Название должно содержать минимум 2 символа. Попробуйте еще раз:"
                )
                return ADDING_CONTACT_NAME
            
            # Сохраняем имя
            context.user_data['contact_creation']['name'] = name
            
            await update.message.reply_text(
                f"✅ Название: <b>{name}</b>\n\n"
                "Теперь введите номер телефона:",
                reply_markup=contact_creation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_PHONE
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки имени контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода телефона контакта"""
        try:
            phone = update.message.text.strip()
            
            # Простая валидация телефона
            import re
            phone_pattern = r'(\+?[78]\s?\(?\d{3}\)?\s?\d{3}[-_]?\d{2}[-_]?\d{2})'
            if not re.match(phone_pattern, phone):
                await update.message.reply_text(
                    "❌ Неверный формат телефона. Используйте формат:\n"
                    "+7 (999) 123-45-67 или 8 (999) 123-45-67\n\n"
                    "Попробуйте еще раз:"
                )
                return ADDING_CONTACT_PHONE
            
            # Сохраняем телефон
            context.user_data['contact_creation']['phone'] = phone
            
            await update.message.reply_text(
                f"✅ Телефон: <b>{phone}</b>\n\n"
                "Введите email (или отправьте '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_EMAIL
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки телефона контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_email_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода email контакта"""
        try:
            email = update.message.text.strip()
            
            if email == '-':
                email = ''
            else:
                # Простая валидация email
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    await update.message.reply_text(
                        "❌ Неверный формат email. Попробуйте еще раз или отправьте '-' чтобы пропустить:"
                    )
                    return ADDING_CONTACT_EMAIL
            
            # Сохраняем email
            context.user_data['contact_creation']['email'] = email
            
            await update.message.reply_text(
                f"✅ Email: <b>{email if email else 'не указан'}</b>\n\n"
                "Введите адрес (или отправьте '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_ADDRESS
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки email контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_address_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода адреса контакта"""
        try:
            address = update.message.text.strip()
            
            if address == '-':
                address = ''
            
            # Сохраняем адрес
            context.user_data['contact_creation']['address'] = address
            
            await update.message.reply_text(
                f"✅ Адрес: <b>{address if address else 'не указан'}</b>\n\n"
                "Введите веб-сайт (или отправьте '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_WEBSITE
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки адреса контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_website_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода веб-сайта контакта"""
        try:
            website = update.message.text.strip()
            
            if website == '-':
                website = ''
            else:
                # Простая валидация веб-сайта
                if not website.startswith(('http://', 'https://', 'www.')):
                    website = 'www.' + website
            
            # Сохраняем веб-сайт
            context.user_data['contact_creation']['website'] = website
            
            await update.message.reply_text(
                f"✅ Веб-сайт: <b>{website if website else 'не указан'}</b>\n\n"
                "Введите описание деятельности (или отправьте '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_DESCRIPTION
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки веб-сайта контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_description_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода описания контакта"""
        try:
            description = update.message.text.strip()
            
            if description == '-':
                description = ''
            
            # Сохраняем описание
            context.user_data['contact_creation']['description'] = description
            
            # Показываем выбор категории
            await update.message.reply_text(
                f"✅ Описание: <b>{description if description else 'не указано'}</b>\n\n"
                "Выберите категорию контакта:",
                reply_markup=contact_categories_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return ADDING_CONTACT_CATEGORY
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки описания контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора категории контакта"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data.startswith("category_"):
                category = query.data.replace("category_", "")
                context.user_data['contact_creation']['category'] = category
                
                # Сохраняем контакт
                contact_data = context.user_data['contact_creation']
                contact_data['type'] = category
                contact_data['tags'] = []
                contact_data['internet_enriched'] = 'false'
                
                # Сохраняем в базу
                if self.knowledge_collector.save_supplier_contact(contact_data):
                    # Отправляем уведомление в Веретево Инфо
                    notification_text = (
                        f"📞 <b>НОВЫЙ КОНТАКТ ДОБАВЛЕН</b>\n\n"
                        f"🏢 <b>{contact_data['name']}</b>\n"
                        f"📱 Телефон: {contact_data['phone']}\n"
                        f"🏷️ Категория: {category}\n"
                        f"👤 Добавил: {update.effective_user.first_name}\n"
                        f"⏰ Время: {datetime.now().strftime('%d.%m %H:%M')}"
                    )
                    
                    await self._send_notification_to_veretevo_info(notification_text, context)
                    
                    # Показываем результат
                    await query.edit_message_text(
                        f"✅ <b>КОНТАКТ УСПЕШНО ДОБАВЛЕН!</b>\n\n"
                        f"🏢 <b>{contact_data['name']}</b>\n"
                        f"📱 Телефон: {contact_data['phone']}\n"
                        f"🏷️ Категория: {category}\n"
                        f"📧 Email: {contact_data['email'] if contact_data['email'] else 'не указан'}\n"
                        f"🏠 Адрес: {contact_data['address'] if contact_data['address'] else 'не указан'}\n"
                        f"🌐 Сайт: {contact_data['website'] if contact_data['website'] else 'не указан'}\n"
                        f"📝 Описание: {contact_data['description'] if contact_data['description'] else 'не указано'}\n\n"
                        f"Контакт автоматически дополнен информацией из интернета!",
                        reply_markup=contacts_menu_keyboard(),
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Очищаем данные создания
                    context.user_data.pop('contact_creation', None)
                    
                    return CONTACTS_MENU
                else:
                    await query.edit_message_text(
                        "❌ Ошибка при сохранении контакта. Попробуйте еще раз.",
                        reply_markup=contacts_menu_keyboard()
                    )
                    return CONTACTS_MENU
            
            return ADDING_CONTACT_CATEGORY
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора категории: {e}")
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END

    async def handle_contact_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода поискового запроса"""
        try:
            search_query = update.message.text.strip()
            
            if not search_query or len(search_query) < 2:
                await update.message.reply_text(
                    "❌ Поисковый запрос должен содержать минимум 2 символа. Попробуйте еще раз:"
                )
                return SEARCHING_CONTACT
            
            # Выполняем поиск
            results = self.knowledge_collector.search_contacts_advanced(search_query)
            
            if not results:
                await update.message.reply_text(
                    f"🔍 <b>ПОИСК: '{search_query}'</b>\n\n"
                    f"ℹ️ По вашему запросу ничего не найдено.\n\n"
                    f"Попробуйте:\n"
                    f"• Изменить поисковый запрос\n"
                    f"• Использовать часть имени или телефона\n"
                    f"• Поиск по категории",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                return CONTACTS_MENU
            
            # Формируем результаты поиска
            search_text = f"🔍 <b>ПОИСК: '{search_query}'</b>\n\n"
            search_text += f"Найдено контактов: {len(results)}\n\n"
            
            for i, contact in enumerate(results[:10], 1):  # Показываем первые 10
                enriched_icon = "🌐" if contact['internet_enriched'] == 'true' else "📞"
                search_text += f"{i}. {enriched_icon} <b>{contact['name']}</b>\n"
                search_text += f"   📱 {contact['phone']}\n"
                search_text += f"   🏷️ {contact['category']}\n"
                if contact['email']:
                    search_text += f"   📧 {contact['email']}\n"
                search_text += "\n"
            
            if len(results) > 10:
                search_text += f"... и еще {len(results) - 10} контактов\n\n"
            
            search_text += "Используйте кнопки ниже для управления:"
            
            await update.message.reply_text(
                search_text,
                reply_markup=contacts_menu_keyboard(),
                parse_mode=ParseMode.HTML
            )
            
            return CONTACTS_MENU
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска контактов: {e}")
            await update.message.reply_text("❌ Произошла ошибка при поиске. Попробуйте еще раз.")
            return ConversationHandler.END

    async def cancel_contact_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции с контактом по команде /cancel"""
        try:
            # Очищаем данные создания
            context.user_data.pop('contact_creation', None)
            
            await update.message.reply_text(
                "❌ Операция отменена.\n\n"
                "Возвращаемся в меню контактов:",
                reply_markup=contacts_menu_keyboard()
            )
            
            return CONTACTS_MENU
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены операции: {e}")
            return ConversationHandler.END

    async def handle_contact_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки отмены при создании контакта"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Очищаем данные создания
            context.user_data.pop('contact_creation', None)
            
            await query.edit_message_text(
                "❌ Создание контакта отменено.\n\n"
                "Возвращаемся в меню контактов:",
                reply_markup=contacts_menu_keyboard()
            )
            
            return CONTACTS_MENU
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены создания контакта: {e}")
            return ConversationHandler.END


def register_contacts_handlers(application: Application) -> None:
    """Регистрация обработчиков команд по контактам"""
    contacts_handler = ContactsHandler()
    
    # Создаем ConversationHandler для управления состояниями
    contacts_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("contacts", contacts_handler.contacts_command),
            MessageHandler(filters.Regex("^📞 Контакты$"), contacts_handler.contacts_button_handler),
            CallbackQueryHandler(contacts_handler.contacts_callback_handler)
        ],
        states={
            ADDING_CONTACT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_name_input)
            ],
            ADDING_CONTACT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_phone_input)
            ],
            ADDING_CONTACT_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_email_input)
            ],
            ADDING_CONTACT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_address_input)
            ],
            ADDING_CONTACT_WEBSITE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_website_input)
            ],
            ADDING_CONTACT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_description_input)
            ],
            ADDING_CONTACT_CATEGORY: [
                CallbackQueryHandler(contacts_handler.handle_contact_category_selection)
            ],
            SEARCHING_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, contacts_handler.handle_contact_search_input)
            ],
            CONTACTS_MENU: [
                CallbackQueryHandler(contacts_handler.contacts_callback_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", contacts_handler.cancel_contact_operation),
            CallbackQueryHandler(contacts_handler.handle_contact_cancel, pattern="^contact_cancel$")
        ]
    )
    
    # Регистрируем ConversationHandler
    application.add_handler(contacts_conversation)
    
    logger.info("✅ Обработчики команд по контактам зарегистрированы с ConversationHandler")
