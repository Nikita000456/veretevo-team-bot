import os
import tempfile
import requests
import json
import base64
from typing import Optional
from pydub import AudioSegment
from config_veretevo import env

class YandexSpeechKitTranscriber:
    def __init__(self, api_key: str = None, folder_id: str = None):
        """
        Инициализация транскрайбера Yandex SpeechKit
        
        Args:
            api_key: API ключ для Yandex SpeechKit (берется из config_veretevo.env или переменной окружения)
            folder_id: ID папки в Yandex Cloud (берется из config_veretevo.env или переменной окружения)
        """
        self.api_key = api_key or env.YANDEX_SPEECHKIT_API_KEY or os.getenv('YANDEX_SPEECHKIT_API_KEY')
        self.folder_id = folder_id or env.YANDEX_FOLDER_ID or os.getenv('YANDEX_FOLDER_ID')
        self.base_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        
        if not self.api_key:
            raise ValueError("Не установлен API ключ Yandex SpeechKit. Установите переменную YANDEX_SPEECHKIT_API_KEY")
        if not self.folder_id:
            raise ValueError("Не установлен Folder ID. Установите переменную YANDEX_FOLDER_ID")

    def convert_audio_to_ogg(self, input_path: str) -> Optional[str]:
        """
        Конвертирует аудиофайл в OGG формат для Yandex SpeechKit
        
        Args:
            input_path: Путь к входному аудиофайлу
            
        Returns:
            Путь к временному OGG файлу или None при ошибке
        """
        try:
            audio = AudioSegment.from_file(input_path)
            # Конвертируем в моно, 48kHz для лучшего качества распознавания
            audio = audio.set_channels(1).set_frame_rate(48000)
            # Нормализуем громкость
            audio = audio.normalize()
            # Убираем тишину в начале и конце
            audio = audio.strip_silence(silence_len=500, silence_thresh=-40)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                # Экспортируем в OGG формат с Opus кодеком
                audio.export(temp_file.name, format='ogg', codec='libopus', parameters=["-ac", "1", "-ar", "48000", "-b:a", "64k"])
                return temp_file.name
        except Exception as e:
            print(f"[ОШИБКА] Не удалось конвертировать аудио: {e}")
            return None

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Транскрибирует аудиофайл через Yandex SpeechKit
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Текст транскрипции или None при ошибке
        """
        try:
            # Проверяем существование файла
            if not os.path.exists(audio_path):
                print(f"[ОШИБКА] Файл не существует: {audio_path}")
                return None
                
            # Проверяем размер файла
            file_size = os.path.getsize(audio_path)
            print(f"[DEBUG] Размер исходного файла: {file_size} байт")
            
            if file_size == 0:
                print(f"[ОШИБКА] Файл пустой: {audio_path}")
                return None
            
            # Отправляем аудиофайл как raw binary data
            url = f"{self.base_url}?folderId={self.folder_id}&lang=ru-RU&model=general:rc&sampleRateHertz=48000&profanityFilter=false&partialResults=false"
            headers = {
                'Authorization': f'Api-Key {self.api_key}',
                'Content-Type': 'application/octet-stream'
            }
            
            print(f"[DEBUG] API URL: {url}")
            print(f"[DEBUG] API Key: {self.api_key[:10]}...")
            print(f"[DEBUG] Folder ID: {self.folder_id}")
            print(f"[DEBUG] Headers: {headers}")
            
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            print(f"[DEBUG] Размер аудио данных: {len(audio_data)} байт")
            print(f"[DEBUG] Первые 100 байт: {audio_data[:100]}")
            
            # Отправляем запрос
            response = requests.post(url, headers=headers, data=audio_data, timeout=30)
            
            print(f"[DEBUG] Получен ответ: статус {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] Ответ API: {result}")
                if 'result' in result:
                    transcript = result['result']
                    print(f"[DEBUG] Транскрипция: '{transcript}'")
                    return transcript
                else:
                    print(f"[ОШИБКА] Неожиданный ответ от API: {result}")
                    return None
            else:
                print(f"[ОШИБКА] Ошибка API: {response.status_code}")
                print(f"[DEBUG] Response text: {response.text}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
                return None
                
        except Exception as e:
            print(f"[ОШИБКА] Не удалось транскрибировать аудио: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return None

    def process_audio_file(self, file_path: str) -> Optional[str]:
        """
        Обрабатывает аудиофайл: конвертирует и транскрибирует
        
        Args:
            file_path: Путь к входному аудиофайлу
            
        Returns:
            Текст транскрипции или None при ошибке
        """
        temp_files = []
        try:
            print(f"[DEBUG] Начинаем обработку файла: {file_path}")
            
            # Конвертируем в OGG
            ogg_path = self.convert_audio_to_ogg(file_path)
            if not ogg_path:
                print(f"[ОШИБКА] Не удалось конвертировать файл: {file_path}")
                return None
            temp_files.append(ogg_path)
            print(f"[DEBUG] Файл конвертирован: {ogg_path}")
            
            # Транскрибируем
            transcript = self.transcribe_audio(ogg_path)
            if transcript:
                print(f"[DEBUG] Транскрипция успешна: '{transcript}'")
            else:
                print(f"[ОШИБКА] Транскрипция не удалась для файла: {ogg_path}")
            return transcript
            
        except Exception as e:
            print(f"[ОШИБКА] Ошибка при обработке аудиофайла: {e}")
            return None
        finally:
            # Удаляем временные файлы
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось удалить временный файл {temp_file}: {e}")

    def test_connection(self) -> bool:
        """
        Тестирует подключение к Yandex SpeechKit API
        
        Returns:
            True если подключение работает, False в противном случае
        """
        try:
            # Создаем минимальный тестовый OGG файл с тишиной
            from pydub import AudioSegment
            
            # Создаем 1 секунду тишины (нулевые сэмплы)
            import numpy as np
            sample_rate = 48000
            duration_ms = 1000
            samples = np.zeros(int(sample_rate * duration_ms / 1000), dtype=np.int16)
            
            # Создаем AudioSegment из numpy массива
            audio = AudioSegment(
                samples.tobytes(), 
                frame_rate=sample_rate,
                sample_width=2, 
                channels=1
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                audio.export(temp_file.name, format='ogg', codec='libopus', parameters=["-ac", "1", "-ar", "48000"])
                
                url = f"{self.base_url}?folderId={self.folder_id}&lang=ru-RU&model=general:rc&sampleRateHertz=48000&profanityFilter=false&partialResults=false"
                headers = {
                    'Authorization': f'Api-Key {self.api_key}',
                    'Content-Type': 'application/octet-stream'
                }
                
                with open(temp_file.name, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                response = requests.post(url, headers=headers, data=audio_data, timeout=10)
                print(f"[DEBUG] Тест подключения: статус {response.status_code}")
                if response.status_code != 200:
                    print(f"[DEBUG] Тест подключения: ответ {response.text}")
                
                # Удаляем временный файл
                os.unlink(temp_file.name)
                
                return response.status_code == 200
            
        except Exception as e:
            print(f"[ОШИБКА] Тест подключения не прошел: {e}")
            return False 