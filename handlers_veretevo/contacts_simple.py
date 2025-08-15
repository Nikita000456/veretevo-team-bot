#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная версия обработчиков команд по управлению контактами
Для тестирования без зависимости от OpenAI
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

logger = logging.getLogger(__name__)

# Разрешенные отделы для работы с контактами
ALLOWED_DEPARTMENTS = ['Ассистенты', 'Руководители', 'Стройка']

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

class MockKnowledgeCollector:
    """Заглушка для KnowledgeCollector для тестирования"""
    
    def __init__(self):
        self.suppliers_database = {}
        self.suppliers_file = "data/suppliers_database.json"
    
    def save_supplier_contact(self, contact_data):
        """Заглушка сохранения контакта"""
        logger.info(f"📞 Мок: Сохранен контакт {contact_data.get('name', 'Unknown')}")
        return True
    
    def get_contacts_by_category(self, category):
        """Заглушка получения контактов по категории"""
        return []
    
    def search_contacts_advanced(self, query):
        """Заглушка поиска контактов"""
        return []

class ContactsHandler:
    """Обработчик команд по контактам"""
    
    def __init__(self):
        # Используем заглушку вместо реального KnowledgeCollector
        self.knowledge_collector = MockKnowledgeCollector()
        self.veretevo_info_chat_id = None
    
    def _check_user_access(self, user_id: int) -> bool:
        """Проверка доступа пользователя к функциям контактов"""
        try:
            if not user_id:
                return False
            
            # Для тестирования разрешаем доступ всем
            logger.info(f"🔓 Тестовый режим: пользователь {user_id} имеет доступ")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа пользователя {user_id}: {e}")
            return False
    
    async def _send_notification_to_veretevo_info(self, message: str, context: ContextTypes.DEFAULT_TYPE):
        """Отправка уведомления в чат Веретево Инфо"""
        try:
            logger.info(f"📢 Мок: Уведомление отправлено: {message[:50]}...")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")
    
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
        await query.edit_message_text(
            "📋 <b>СПИСОК КОНТАКТОВ</b>\n\n"
            "ℹ️ В базе пока нет контактов.\n"
            "Добавьте первый контакт!",
            reply_markup=contacts_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
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
        await query.edit_message_text(
            "📤 <b>ЭКСПОРТ КОНТАКТОВ</b>\n\n"
            "ℹ️ В базе нет контактов для экспорта.",
            reply_markup=contacts_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_main_menu(self, query, context):
        """Возврат в главное меню"""
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=main_menu_keyboard("private", query.from_user.id)
        )
    
    async def _handle_category_selection(self, query, context, callback_data):
        """Обработка выбора категории"""
        category = callback_data.replace("category_", "")
        category_names = {
            'supplier': 'Поставщики',
            'contractor': 'Подрядчики', 
            'employee': 'Сотрудники'
        }
        
        await query.edit_message_text(
            f"🏷️ <b>КАТЕГОРИЯ: {category_names.get(category, category)}</b>\n\n"
            f"ℹ️ В этой категории пока нет контактов.",
            reply_markup=contact_categories_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    # Добавляем недостающие методы для ConversationHandler
    async def handle_contact_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода названия контакта"""
        try:
            name = update.message.text.strip()
            if len(name) < 2:
                await update.message.reply_text(
                    "❌ Название должно содержать минимум 2 символа. Попробуйте еще раз:",
                    reply_markup=contact_creation_keyboard()
                )
                return ADDING_CONTACT_NAME
            
            # Сохраняем название
            context.user_data['contact_creation']['name'] = name
            
            await update.message.reply_text(
                "📱 Теперь введите номер телефона:",
                reply_markup=contact_creation_keyboard()
            )
            return ADDING_CONTACT_PHONE
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки названия контакта: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END
    
    async def handle_contact_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода телефона контакта"""
        try:
            phone = update.message.text.strip()
            # Простая валидация телефона
            if not (phone.startswith('+7') or phone.startswith('8')) or len(phone) < 10:
                await update.message.reply_text(
                    "❌ Неверный формат телефона. Используйте формат +7 (999) 123-45-67 или 8 (999) 123-45-67. Попробуйте еще раз:",
                    reply_markup=contact_creation_keyboard()
                )
                return ADDING_CONTACT_PHONE
            
            # Сохраняем телефон
            context.user_data['contact_creation']['phone'] = phone
            
            await update.message.reply_text(
                "📧 Введите email (или '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard()
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
            elif '@' not in email:
                await update.message.reply_text(
                    "❌ Неверный формат email. Попробуйте еще раз или введите '-' чтобы пропустить:",
                    reply_markup=contact_creation_keyboard()
                )
                return ADDING_CONTACT_EMAIL
            
            # Сохраняем email
            context.user_data['contact_creation']['email'] = email
            
            await update.message.reply_text(
                "📍 Введите адрес (или '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard()
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
                "🌐 Введите веб-сайт (или '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard()
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
            elif website and not website.startswith(('http://', 'https://', 'www.')):
                website = 'www.' + website
            
            # Сохраняем веб-сайт
            context.user_data['contact_creation']['website'] = website
            
            await update.message.reply_text(
                "📝 Введите описание (или '-' чтобы пропустить):",
                reply_markup=contact_creation_keyboard()
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
                "🏷️ Выберите категорию контакта:",
                reply_markup=contact_categories_keyboard()
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
            
            if query.data.startswith('category_'):
                category = query.data.replace('category_', '')
                context.user_data['contact_creation']['category'] = category
                
                # Сохраняем контакт
                contact_data = context.user_data['contact_creation']
                success = self.knowledge_collector.save_supplier_contact(contact_data)
                
                if success:
                    await query.edit_message_text(
                        f"✅ Контакт успешно добавлен!\n\n"
                        f"🏢 Название: {contact_data['name']}\n"
                        f"📱 Телефон: {contact_data['phone']}\n"
                        f"🏷️ Категория: {category}",
                        reply_markup=contacts_menu_keyboard()
                    )
                    
                    # Отправляем уведомление
                    notification = f"📞 НОВЫЙ КОНТАКТ ДОБАВЛЕН\n\n🏢 {contact_data['name']}\n📱 {contact_data['phone']}\n🏷️ {category}"
                    await self._send_notification_to_veretevo_info(notification, context)
                    
                    # Очищаем данные
                    context.user_data.pop('contact_creation', None)
                    return ConversationHandler.END
                else:
                    await query.edit_message_text(
                        "❌ Ошибка при сохранении контакта. Попробуйте еще раз.",
                        reply_markup=contacts_menu_keyboard()
                    )
                    return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "❌ Неверная категория. Попробуйте еще раз.",
                    reply_markup=contact_categories_keyboard()
                )
                return ADDING_CONTACT_CATEGORY
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора категории: {e}")
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")
            return ConversationHandler.END
    
    async def handle_contact_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка поиска контактов"""
        try:
            query_text = update.message.text.strip()
            if len(query_text) < 2:
                await update.message.reply_text(
                    "❌ Поисковый запрос должен содержать минимум 2 символа. Попробуйте еще раз:",
                    reply_markup=contacts_menu_keyboard()
                )
                return SEARCHING_CONTACT
            
            # Ищем контакты
            results = self.knowledge_collector.search_contacts_advanced(query_text)
            
            if results:
                # Показываем результаты
                result_text = f"🔍 Результаты поиска по запросу '{query_text}':\n\n"
                for i, contact in enumerate(results[:10], 1):
                    result_text += f"{i}. {contact.get('name', 'N/A')}\n"
                    result_text += f"   📱 {contact.get('phone', 'N/A')}\n"
                    result_text += f"   📧 {contact.get('email', 'N/A')}\n"
                    result_text += f"   🏷️ {contact.get('category', 'N/A')}\n\n"
                
                await update.message.reply_text(
                    result_text,
                    reply_markup=contacts_menu_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"🔍 По запросу '{query_text}' ничего не найдено.\n\n"
                    f"💡 Попробуйте изменить поисковый запрос или добавить новый контакт.",
                    reply_markup=contacts_menu_keyboard()
                )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска контактов: {e}")
            await update.message.reply_text("❌ Произошла ошибка при поиске. Попробуйте еще раз.")
            return ConversationHandler.END
    
    async def cancel_contact_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции с контактом"""
        try:
            # Очищаем данные
            context.user_data.pop('contact_creation', None)
            
            await update.message.reply_text(
                "❌ Операция отменена.",
                reply_markup=contacts_menu_keyboard()
            )
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены операции: {e}")
            return ConversationHandler.END
    
    async def handle_contact_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки отмены"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Очищаем данные
            context.user_data.pop('contact_creation', None)
            
            await query.edit_message_text(
                "❌ Операция отменена.",
                reply_markup=contacts_menu_keyboard()
            )
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены операции: {e}")
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
