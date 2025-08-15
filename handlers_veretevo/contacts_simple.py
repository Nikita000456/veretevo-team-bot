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
