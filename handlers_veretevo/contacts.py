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

class KnowledgeCollector:
    """Реальный KnowledgeCollector для работы с контактами"""
    
    def __init__(self):
        self.suppliers_database = {}
        self.suppliers_file = "data/suppliers_database.json"
        self._load_suppliers_database()
    
    def _load_suppliers_database(self):
        """Загрузка базы поставщиков"""
        try:
            if os.path.exists(self.suppliers_file):
                with open(self.suppliers_file, 'r', encoding='utf-8') as f:
                    self.suppliers_database = json.load(f)
                logger.info(f"📞 Загружена база поставщиков: {len(self.suppliers_database)} контактов")
            else:
                logger.info("📞 Создана новая база поставщиков")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки базы поставщиков: {e}")
            self.suppliers_database = {}
    
    def _save_suppliers_database(self):
        """Сохранение базы поставщиков"""
        try:
            with open(self.suppliers_file, 'w', encoding='utf-8') as f:
                json.dump(self.suppliers_database, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения базы поставщиков: {e}")
            return False
    
    def save_supplier_contact(self, contact_data):
        """Сохранение контакта поставщика"""
        try:
            phone = contact_data.get('phone', '').strip()
            if not phone:
                return False
            
            # Определяем категорию контакта
            category = contact_data.get('category', 'supplier')
            if not category:
                category = 'supplier'
            
            # Проверяем, есть ли уже такой контакт
            if phone in self.suppliers_database:
                # Обновляем существующий
                self.suppliers_database[phone].update({
                    'last_updated': datetime.now().isoformat(),
                    'update_count': self.suppliers_database[phone].get('update_count', 0) + 1
                })
                logger.info(f"📞 Обновлен контакт {category}: {contact_data.get('name', 'Unknown')}")
            else:
                # Добавляем новый
                self.suppliers_database[phone] = {
                    'name': contact_data.get('name', 'Unknown'),
                    'phone': phone,
                    'email': contact_data.get('email', ''),
                    'address': contact_data.get('address', ''),
                    'website': contact_data.get('website', ''),
                    'description': contact_data.get('description', ''),
                    'type': contact_data.get('type', 'supplier'),
                    'category': category,
                    'tags': contact_data.get('tags', []),
                    'first_added': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'update_count': 1,
                    'internet_enriched': contact_data.get('internet_enriched', 'false')
                }
                logger.info(f"📞 Добавлен новый контакт {category}: {contact_data.get('name', 'Unknown')}")
            
            # Сохраняем базу поставщиков
            return self._save_suppliers_database()
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения контакта поставщика: {e}")
            return False
    
    def get_contacts_by_category(self, category):
        """Получение контактов по категории"""
        try:
            contacts = []
            for phone, data in self.suppliers_database.items():
                if data.get('category') == category:
                    contacts.append({
                        'name': data.get('name', 'Unknown'),
                        'phone': phone,
                        'email': data.get('email', ''),
                        'address': data.get('address', ''),
                        'website': data.get('website', ''),
                        'description': data.get('description', ''),
                        'category': data.get('category', 'supplier')
                    })
            return contacts
        except Exception as e:
            logger.error(f"❌ Ошибка получения контактов по категории: {e}")
            return []
    
    def search_contacts_advanced(self, query):
        """Поиск контактов по ключевому слову"""
        try:
            query_lower = query.lower()
            matching_contacts = []
            
            for phone, data in self.suppliers_database.items():
                name = data.get('name', '').lower()
                phone_str = phone.lower()
                description = data.get('description', '').lower()
                
                if (query_lower in name or 
                    query_lower in phone_str or
                    query_lower in description):
                    matching_contacts.append({
                        'name': data.get('name', 'Unknown'),
                        'phone': phone,
                        'email': data.get('email', ''),
                        'address': data.get('address', ''),
                        'website': data.get('website', ''),
                        'description': data.get('description', ''),
                        'category': data.get('category', 'supplier')
                    })
            
            return matching_contacts
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска контактов: {e}")
            return []
    
    def get_all_contacts(self):
        """Получение всех контактов"""
        try:
            contacts = []
            for phone, data in self.suppliers_database.items():
                contacts.append({
                    'name': data.get('name', 'Unknown'),
                    'phone': phone,
                    'email': data.get('email', ''),
                    'address': data.get('address', ''),
                    'website': data.get('website', ''),
                    'description': data.get('description', ''),
                    'category': data.get('category', 'supplier')
                })
            return contacts
        except Exception as e:
            logger.error(f"❌ Ошибка получения всех контактов: {e}")
            return []

class ContactsHandler:
    """Обработчик команд по контактам"""
    
    def __init__(self):
        # Используем заглушку вместо реального KnowledgeCollector
        self.knowledge_collector = KnowledgeCollector()
        self.veretevo_info_chat_id = None
    
    async def _safe_edit_message(self, query, text, reply_markup=None, parse_mode=None, fallback_message=""):
        """Безопасное редактирование сообщения с обработкой ошибки 'Message is not modified'"""
        try:
            kwargs = {"text": text}
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
                
            await query.edit_message_text(**kwargs)
            return True
        except Exception as e:
            if "Message is not modified" in str(e):
                # Сообщение уже имеет нужное содержимое
                await query.answer(fallback_message or "Содержимое уже отображается")
                return True
            else:
                # Другая ошибка
                logger.error(f"❌ Ошибка при редактировании сообщения: {e}")
                await query.answer("❌ Произошла ошибка при обновлении сообщения")
                return False
    
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
            
            logger.info(f"📱 Обработка callback: {callback_data} от пользователя {user_id}")
            
            # Проверяем права доступа
            if not self._check_user_access(user_id):
                await self._safe_edit_message(
                    query,
                    "🚫 У вас нет доступа к управлению контактами.\n"
                    "Доступ разрешен только для отделов: Ассистенты, Руководители, Стройка.",
                    fallback_message="Доступ запрещен"
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
                logger.warning(f"⚠️ Неизвестный callback: {callback_data}")
                await self._safe_edit_message(
                    query,
                    "❌ Неизвестная команда",
                    fallback_message="Команда не распознана"
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")
            try:
                # Пытаемся отредактировать сообщение с ошибкой
                await self._safe_edit_message(
                    query,
                    "❌ Произошла ошибка при обработке команды",
                    fallback_message="❌ Произошла ошибка при обработке команды"
                )
            except Exception as edit_error:
                # Если не удается отредактировать, просто отвечаем на callback
                logger.error(f"❌ Не удалось отредактировать сообщение с ошибкой: {edit_error}")
                try:
                    await query.answer("❌ Произошла ошибка при обработке команды")
                except:
                    pass
    
    async def _handle_find_contact(self, query, context):
        """Обработка поиска контакта"""
        success = await self._safe_edit_message(
            query,
            "🔍 <b>ПОИСК КОНТАКТА</b>\n\n"
            "Введите имя, телефон или описание для поиска:",
            parse_mode=ParseMode.HTML,
            fallback_message="Поиск контакта уже активен"
        )
        
        if success:
            # Переходим к состоянию поиска
            return SEARCHING_CONTACT
        else:
            return ConversationHandler.END
    
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
        
        success = await self._safe_edit_message(
            query,
            "➕ <b>ДОБАВЛЕНИЕ КОНТАКТА</b>\n\n"
            "Введите название компании или имя контакта:",
            parse_mode=ParseMode.HTML,
            fallback_message="Добавление контакта уже активно"
        )
        
        if success:
            # Переходим к состоянию ввода имени
            return ADDING_CONTACT_NAME
        else:
            return ConversationHandler.END
    
    async def _handle_list_contacts(self, query, context):
        """Обработка списка всех контактов"""
        try:
            # Получаем все контакты
            all_contacts = self.knowledge_collector.get_all_contacts()
            
            if all_contacts:
                # Формируем список контактов
                contacts_text = "📋 <b>СПИСОК ВСЕХ КОНТАКТОВ</b>\n\n"
                
                for i, contact in enumerate(all_contacts, 1):
                    contacts_text += f"{i}. <b>{contact['name']}</b>\n"
                    contacts_text += f"   📱 {contact['phone']}\n"
                    if contact.get('email'):
                        contacts_text += f"   📧 {contact['email']}\n"
                    if contact.get('address'):
                        contacts_text += f"   📍 {contact['address']}\n"
                    if contact.get('website'):
                        contacts_text += f"   🌐 {contact['website']}\n"
                    if contact.get('description'):
                        contacts_text += f"   📝 {contact['description']}\n"
                    contacts_text += f"   🏷️ {contact['category']}\n\n"
                
                # Ограничиваем длину сообщения
                if len(contacts_text) > 4000:
                    contacts_text = contacts_text[:4000] + "\n\n... (показаны первые контакты)"
                
                await self._safe_edit_message(
                    query,
                    contacts_text,
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message="Список контактов уже отображается"
                )
            else:
                await self._safe_edit_message(
                    query,
                    "📋 <b>СПИСОК КОНТАКТОВ</b>\n\n"
                    "ℹ️ В базе пока нет контактов.\n"
                    "Добавьте первый контакт!",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message="Список контактов уже отображается"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка при показе списка контактов: {e}")
            await self._safe_edit_message(
                query,
                "❌ Произошла ошибка при загрузке списка контактов",
                reply_markup=contacts_menu_keyboard(),
                fallback_message="Ошибка загрузки"
            )
    
    async def _handle_show_categories(self, query, context):
        """Показ категорий контактов"""
        try:
            # Получаем контакты по категориям
            suppliers = self.knowledge_collector.get_contacts_by_category('supplier')
            contractors = self.knowledge_collector.get_contacts_by_category('contractor')
            employees = self.knowledge_collector.get_contacts_by_category('employee')
            
            categories_text = "🏷️ <b>КАТЕГОРИИ КОНТАКТОВ</b>\n\n"
            categories_text += f"🏭 <b>Поставщики:</b> {len(suppliers)} контактов\n"
            categories_text += f"🏗️ <b>Подрядчики:</b> {len(contractors)} контактов\n"
            categories_text += f"👥 <b>Сотрудники:</b> {len(employees)} контактов\n\n"
            categories_text += "Выберите категорию для просмотра контактов:"
            
            await self._safe_edit_message(
                query,
                categories_text,
                reply_markup=contact_categories_keyboard(),
                parse_mode=ParseMode.HTML,
                fallback_message="Категории уже отображаются"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при показе категорий: {e}")
            await self._safe_edit_message(
                query,
                "❌ Произошла ошибка при загрузке категорий",
                reply_markup=contact_categories_keyboard(),
                fallback_message="Ошибка загрузки"
            )
    
    async def _handle_export_contacts(self, query, context):
        """Экспорт контактов"""
        try:
            all_contacts = self.knowledge_collector.get_all_contacts()
            
            if all_contacts:
                export_text = "📤 <b>ЭКСПОРТ КОНТАКТОВ</b>\n\n"
                export_text += f"Всего контактов: {len(all_contacts)}\n\n"
                
                for contact in all_contacts:
                    export_text += f"• {contact['name']} - {contact['phone']}\n"
                
                # Ограничиваем длину сообщения
                if len(export_text) > 4000:
                    export_text = export_text[:4000] + "\n\n... (показаны первые контакты)"
                
                await self._safe_edit_message(
                    query,
                    export_text,
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message="Экспорт контактов уже отображается"
                )
            else:
                await self._safe_edit_message(
                    query,
                    "📤 <b>ЭКСПОРТ КОНТАКТОВ</b>\n\n"
                    "ℹ️ В базе нет контактов для экспорта.",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message="Экспорт контактов уже отображается"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка при экспорте контактов: {e}")
            await self._safe_edit_message(
                query,
                "❌ Произошла ошибка при экспорте контактов",
                reply_markup=contacts_menu_keyboard(),
                fallback_message="Ошибка экспорта"
            )
    
    async def _handle_main_menu(self, query, context):
        """Возврат в главное меню"""
        await self._safe_edit_message(
            query,
            "Главное меню:",
            reply_markup=main_menu_keyboard("private", query.from_user.id),
            fallback_message="Главное меню уже отображается"
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
            
            # Получаем контакты по выбранной категории
            contacts = self.knowledge_collector.get_contacts_by_category(category)
            
            if contacts:
                category_text = f"🏷️ <b>КАТЕГОРИЯ: {category_names.get(category, category)}</b>\n\n"
                category_text += f"Найдено контактов: {len(contacts)}\n\n"
                
                for i, contact in enumerate(contacts[:10], 1):  # Показываем первые 10
                    category_text += f"{i}. <b>{contact['name']}</b>\n"
                    category_text += f"   📱 {contact['phone']}\n"
                    if contact.get('email'):
                        category_text += f"   📧 {contact['email']}\n"
                    if contact.get('description'):
                        category_text += f"   📝 {contact['description']}\n"
                    category_text += "\n"
                
                if len(contacts) > 10:
                    category_text += f"... и еще {len(contacts) - 10} контактов"
                
                # Ограничиваем длину сообщения
                if len(category_text) > 4000:
                    category_text = category_text[:4000] + "\n\n... (показаны первые контакты)"
                
                await self._safe_edit_message(
                    query,
                    category_text,
                    reply_markup=contact_categories_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message=f"Категория {category_names.get(category, category)} уже отображается"
                )
            else:
                await self._safe_edit_message(
                    query,
                    f"🏷️ <b>КАТЕГОРИЯ: {category_names.get(category, category)}</b>\n\n"
                    f"ℹ️ В этой категории пока нет контактов.",
                    reply_markup=contact_categories_keyboard(),
                    parse_mode=ParseMode.HTML,
                    fallback_message=f"Категория {category_names.get(category, category)} уже отображается"
                )
        except Exception as e:
            logger.error(f"❌ Ошибка при выборе категории: {e}")
            await self._safe_edit_message(
                query,
                "❌ Произошла ошибка при загрузке категории",
                reply_markup=contact_categories_keyboard(),
                fallback_message="Произошла ошибка"
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
                    await self._safe_edit_message(
                        query,
                        f"✅ Контакт успешно добавлен!\n\n"
                        f"🏢 Название: {contact_data['name']}\n"
                        f"📱 Телефон: {contact_data['phone']}\n"
                        f"🏷️ Категория: {category}",
                        reply_markup=contacts_menu_keyboard(),
                        fallback_message="Контакт успешно добавлен"
                    )
                    
                    # Отправляем уведомление
                    notification = f"📞 НОВЫЙ КОНТАКТ ДОБАВЛЕН\n\n🏢 {contact_data['name']}\n📱 {contact_data['phone']}\n🏷️ {category}"
                    await self._send_notification_to_veretevo_info(notification, context)
                    
                    # Очищаем данные
                    context.user_data.pop('contact_creation', None)
                    return ConversationHandler.END
                else:
                    await self._safe_edit_message(
                        query,
                        "❌ Ошибка при сохранении контакта. Попробуйте еще раз.",
                        reply_markup=contacts_menu_keyboard(),
                        fallback_message="Ошибка при сохранении контакта"
                    )
                    return ConversationHandler.END
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Неверная категория. Попробуйте еще раз.",
                    reply_markup=contact_categories_keyboard(),
                    fallback_message="Неверная категория"
                )
                return ADDING_CONTACT_CATEGORY
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора категории: {e}")
            await self._safe_edit_message(
                query,
                "❌ Произошла ошибка. Попробуйте еще раз.",
                fallback_message="Произошла ошибка"
            )
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
                result_text = f"🔍 <b>Результаты поиска по запросу '{query_text}':</b>\n\n"
                
                for i, contact in enumerate(results[:10], 1):
                    result_text += f"{i}. <b>{contact.get('name', 'N/A')}</b>\n"
                    result_text += f"   📱 {contact.get('phone', 'N/A')}\n"
                    if contact.get('email'):
                        result_text += f"   📧 {contact.get('email', 'N/A')}\n"
                    if contact.get('address'):
                        result_text += f"   📍 {contact.get('address', 'N/A')}\n"
                    if contact.get('website'):
                        result_text += f"   🌐 {contact.get('website', 'N/A')}\n"
                    if contact.get('description'):
                        result_text += f"   📝 {contact.get('description', 'N/A')}\n"
                    result_text += f"   🏷️ {contact.get('category', 'N/A')}\n\n"
                
                # Ограничиваем длину сообщения
                if len(result_text) > 4000:
                    result_text = result_text[:4000] + "\n\n... (показаны первые результаты)"
                
                await update.message.reply_text(
                    result_text,
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"🔍 <b>Поиск по запросу '{query_text}'</b>\n\n"
                    f"ℹ️ Ничего не найдено.\n\n"
                    f"💡 Попробуйте:\n"
                    f"   • Изменить поисковый запрос\n"
                    f"   • Использовать часть имени или телефона\n"
                    f"   • Добавить новый контакт",
                    reply_markup=contacts_menu_keyboard(),
                    parse_mode=ParseMode.HTML
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
            
            await self._safe_edit_message(
                query,
                "❌ Операция отменена.",
                reply_markup=contacts_menu_keyboard(),
                fallback_message="Операция уже отменена"
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
