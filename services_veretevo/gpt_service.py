import json
import os
import logging
import asyncio
import threading
import time
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches
import requests
from config_veretevo.constants import GENERAL_DIRECTOR_ID
from config_veretevo.env import YANDEX_GPT_API_KEY

class GPTService:
    def __init__(self):
        self.answers_file = "data/answers.json"
        self.answers_cache = {}
        self.cache_lock = threading.Lock()
        self.last_save_time = time.time()
        self.autosave_interval = 600  # 10 минут
        
        # Создаем директорию data если её нет
        os.makedirs("data", exist_ok=True)
        
        # Загружаем базу знаний при инициализации
        self._load_answers()
        
        # Запускаем автосохранение в фоне
        self._start_autosave()
    
    def _load_answers(self):
        """Загружает базу знаний из файла в память"""
        try:
            if os.path.exists(self.answers_file):
                with open(self.answers_file, 'r', encoding='utf-8') as f:
                    self.answers_cache = json.load(f)
                logging.info(f"✅ Загружено {len(self.answers_cache)} записей из базы знаний")
            else:
                self.answers_cache = {}
                logging.info("✅ Создана новая база знаний")
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки базы знаний: {e}")
            self.answers_cache = {}
    
    def _save_answers(self):
        """Сохраняет базу знаний на диск"""
        try:
            with self.cache_lock:
                with open(self.answers_file, 'w', encoding='utf-8') as f:
                    json.dump(self.answers_cache, f, ensure_ascii=False, indent=2)
                self.last_save_time = time.time()
                logging.info(f"✅ База знаний сохранена ({len(self.answers_cache)} записей)")
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения базы знаний: {e}")
    
    def _start_autosave(self):
        """Запускает автосохранение в фоне"""
        def autosave_worker():
            while True:
                time.sleep(self.autosave_interval)
                if time.time() - self.last_save_time > self.autosave_interval:
                    self._save_answers()
        
        autosave_thread = threading.Thread(target=autosave_worker, daemon=True)
        autosave_thread.start()
    
    def find_similar_question(self, question: str, threshold: float = 0.6) -> Optional[Dict]:
        """Ищет похожий вопрос в базе знаний"""
        if not self.answers_cache:
            return None
        
        # Получаем все вопросы из базы
        questions = list(self.answers_cache.keys())
        
        # Ищем похожие вопросы
        matches = get_close_matches(question.lower(), [q.lower() for q in questions], n=1, cutoff=threshold)
        
        if matches:
            # Находим оригинальный вопрос (с правильным регистром)
            for original_q in questions:
                if original_q.lower() == matches[0]:
                    return {
                        "question": original_q,
                        "answer": self.answers_cache[original_q]["answer"],
                        "department": self.answers_cache[original_q].get("department", ""),
                        "similarity": matches[0]
                    }
        
        return None
    
    async def generate_gpt_response(self, question: str, context: str = "") -> str:
        """Генерирует ответ с помощью Yandex GPT"""
        try:
            # Получаем API ключ из переменных окружения
            api_key = YANDEX_GPT_API_KEY
            if not api_key:
                return "❌ Ошибка: API ключ Yandex GPT не настроен"
            
            # Формируем промпт с учетом отдела
            department_context = {
                "security": "отдел охраны и безопасности",
                "assistants": "отдел ассистентов и помощников", 
                "carpenters": "отдел плотников и столяров",
                "maintenance": "отдел технического обслуживания",
                "tech": "технический отдел",
                "maids": "отдел горничных и уборки",
                "reception": "отдел ресепшена и администрации",
                "finance": "финансовый отдел"
            }
            
            # Извлекаем отдел из контекста
            department = context.replace("Отдел: ", "") if context.startswith("Отдел: ") else ""
            dept_name = department_context.get(department, "общий отдел")
            
            prompt = f"""
            Ты помощник директора компании Veretevo. Отвечай от имени директора кратко, профессионально и по делу.

            Контекст: Вопрос задан в {dept_name}.
            Вопрос сотрудника: {question}

            Правила ответа:
            1. Отвечай от имени директора (используй "я", "мне", "мы")
            2. Будь конкретным и давай четкие указания
            3. Если нужно время на размышление - скажи об этом
            4. Если вопрос требует дополнительной информации - попроси уточнить
            5. Для отдела охраны - особое внимание безопасности
            6. Для технических отделов - учитывай специфику работы
            7. Для финансовых вопросов - будь осторожен с обещаниями

            Сгенерируй подходящий ответ директора:
            """
            
            # Вызываем Yandex GPT API
            headers = {
                "Authorization": f"Api-Key {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "modelUri": "gpt://b1g8c7c7c7c7c7c7c7c7/yandexgpt-lite",
                "completionOptions": {
                    "temperature": 0.6,
                    "maxTokens": 200
                },
                "messages": [
                    {
                        "role": "user",
                        "text": prompt
                    }
                ]
            }
            
            response = requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["result"]["alternatives"][0]["message"]["text"].strip()
            else:
                logging.error(f"❌ Ошибка API Yandex GPT: {response.status_code} - {response.text}")
                return "❌ Ошибка генерации ответа"
                
        except Exception as e:
            logging.error(f"❌ Ошибка генерации GPT ответа: {e}")
            return "❌ Ошибка генерации ответа"
    
    async def get_smart_response(self, question: str, department: str = "") -> Dict:
        """Получает умный ответ: сначала ищет в базе, потом генерирует"""
        
        # 1. Ищем похожий вопрос в базе знаний
        similar = self.find_similar_question(question)
        
        if similar:
            return {
                "type": "from_cache",
                "answer": similar["answer"],
                "department": similar["department"],
                "similarity": similar["similarity"]
            }
        
        # 2. Генерируем новый ответ через GPT
        context = f"Отдел: {department}" if department else ""
        gpt_answer = await self.generate_gpt_response(question, context)
        
        return {
            "type": "generated",
            "answer": gpt_answer,
            "department": department
        }
    
    def save_answer_template(self, question: str, answer: str, department: str = "") -> bool:
        """Сохраняет ответ в базу знаний"""
        try:
            with self.cache_lock:
                self.answers_cache[question] = {
                    "answer": answer,
                    "department": department,
                    "created_at": time.time()
                }
            
            # Сохраняем на диск
            self._save_answers()
            logging.info(f"✅ Ответ сохранен в базу знаний: {question[:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения ответа: {e}")
            return False
    
    def get_answer_variants(self, question: str) -> List[Dict]:
        """Определяет возможные варианты ответа для кнопок"""
        question_lower = question.lower()
        
        # Ключевые слова для простых Да/Нет вопросов
        yes_no_keywords = ["можно", "нужно", "правильно", "хорошо", "верно", "да", "нет", "разрешить", "допустить", "стоит", "должен"]
        
        variants = []
        
        # Только Да/Нет для простых вопросов
        if any(keyword in question_lower for keyword in yes_no_keywords):
            variants.extend([
                {"text": "✅ Да", "callback_data": "gpt_yes"},
                {"text": "❌ Нет", "callback_data": "gpt_no"}
            ])
        
        # Для всех остальных вопросов - только GPT-анализ
        else:
            variants.extend([
                {"text": "🤖 GPT-анализ", "callback_data": "gpt_analyze"}
            ])
        
        return variants
    
    def get_cache_stats(self) -> Dict:
        """Возвращает статистику базы знаний"""
        return {
            "total_answers": len(self.answers_cache),
            "last_save": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_save_time)),
            "file_size": os.path.getsize(self.answers_file) if os.path.exists(self.answers_file) else 0
        }

# Глобальный экземпляр сервиса
gpt_service = GPTService() 