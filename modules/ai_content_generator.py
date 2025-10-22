"""
Модуль для генерации контента книги с использованием ИИ API.

Поддерживает OpenAI GPT и Anthropic Claude для генерации:
- Заголовков книг
- Описаний и аннотаций
- Оглавления (структуры глав)
- Контента для каждой главы
"""

import logging
import yaml
import os
from typing import Dict, List, Any, Optional
import re

# Настройка логирования
logger = logging.getLogger(__name__)

# Попытка импорта ИИ библиотек
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not available. Install with: pip install anthropic")


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Загружает конфигурационный файл YAML.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Словарь с конфигурацией
        
    Raises:
        FileNotFoundError: Если файл не найден
        yaml.YAMLError: Если файл содержит некорректный YAML
    """
    try:
        logger.info(f"Загрузка конфигурации из {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.debug(f"Конфигурация успешно загружена: {config.get('project', {}).get('name', 'Unknown')}")
        return config
    except FileNotFoundError:
        logger.error(f"Файл конфигурации не найден: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Ошибка парсинга YAML: {e}")
        raise


def _extract_key_themes(transcript: str, max_themes: int = 5) -> List[str]:
    """
    Извлекает ключевые темы из транскрипции для анализа.
    
    Args:
        transcript: Текст транскрипции
        max_themes: Максимальное количество тем
        
    Returns:
        Список ключевых тем
    """
    # Простой анализ: извлечение наиболее частых существительных
    # В реальной реализации можно использовать NLP библиотеки
    words = re.findall(r'\b[А-Яа-яA-Za-z]{4,}\b', transcript.lower())
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Сортируем по частоте
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    themes = [word for word, freq in sorted_words[:max_themes]]
    
    logger.debug(f"Извлечены ключевые темы: {themes}")
    return themes


def _call_openai_gpt(prompt: str, config: Dict[str, Any]) -> str:
    """
    Вызывает OpenAI GPT API для генерации текста.
    
    Args:
        prompt: Промпт для модели
        config: Конфигурация с параметрами API
        
    Returns:
        Сгенерированный текст
        
    Raises:
        Exception: При ошибках API
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI library not installed")
    
    try:
        # Получение API ключа из переменных окружения
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
        
        client = openai.OpenAI(api_key=api_key)
        
        model = config.get('ai', {}).get('content_model', 'gpt-4o')
        temperature = config.get('ai', {}).get('temperature', 0.7)
        
        logger.debug(f"Вызов OpenAI GPT модели: {model}")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Вы - профессиональный автор и редактор книг, работающий для бренда SSVproff."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        result = response.choices[0].message.content
        logger.debug(f"Получен ответ от OpenAI (длина: {len(result)} символов)")
        return result
        
    except openai.APIError as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise
    except openai.RateLimitError as e:
        logger.error(f"Превышен лимит запросов OpenAI: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при вызове OpenAI: {e}")
        raise


def _call_anthropic_claude(prompt: str, config: Dict[str, Any]) -> str:
    """
    Вызывает Anthropic Claude API для генерации текста.
    
    Args:
        prompt: Промпт для модели
        config: Конфигурация с параметрами API
        
    Returns:
        Сгенерированный текст
        
    Raises:
        Exception: При ошибках API
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("Anthropic library not installed")
    
    try:
        # Получение API ключа из переменных окружения
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY не установлен в переменных окружения")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        model = config.get('ai', {}).get('content_model', 'claude-3-opus-20240229')
        temperature = config.get('ai', {}).get('temperature', 0.7)
        
        logger.debug(f"Вызов Anthropic Claude модели: {model}")
        
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.content[0].text
        logger.debug(f"Получен ответ от Claude (длина: {len(result)} символов)")
        return result
        
    except anthropic.APIError as e:
        logger.error(f"Ошибка Anthropic API: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при вызове Anthropic: {e}")
        raise


def _call_ai_model(prompt: str, config: Dict[str, Any]) -> str:
    """
    Универсальная функция для вызова ИИ модели в зависимости от провайдера.
    
    Args:
        prompt: Промпт для модели
        config: Конфигурация с параметрами API
        
    Returns:
        Сгенерированный текст
        
    Raises:
        ValueError: Если провайдер не поддерживается
    """
    provider = config.get('ai', {}).get('content_provider', 'openai_gpt')
    
    if provider == 'openai_gpt':
        return _call_openai_gpt(prompt, config)
    elif provider == 'anthropic_claude':
        return _call_anthropic_claude(prompt, config)
    else:
        raise ValueError(f"Неподдерживаемый провайдер ИИ: {provider}")


def _generate_title(transcript: str, config: Dict[str, Any]) -> str:
    """
    Генерирует заголовок книги на основе транскрипции.
    
    Args:
        transcript: Текст транскрипции или идеи
        config: Конфигурация книги
        
    Returns:
        Сгенерированный заголовок
    """
    book_type = config.get('book', {}).get('type', 'scientific')
    audience = config.get('book', {}).get('target_audience', 'students')
    language = config.get('book', {}).get('language', 'ru')
    
    prompt = f"""
На основе следующего текста создайте короткий и запоминающийся заголовок для книги типа "{book_type}" для аудитории "{audience}".
Заголовок должен быть на языке: {language}.
Заголовок должен быть ёмким, профессиональным и отражать суть материала.

Текст:
{transcript[:2000]}...

Верните ТОЛЬКО заголовок, без кавычек и дополнительных комментариев.
"""
    
    logger.info("Генерация заголовка книги...")
    title = _call_ai_model(prompt, config).strip().strip('"').strip("'")
    logger.info(f"Сгенерирован заголовок: {title}")
    return title


def _generate_description(transcript: str, title: str, config: Dict[str, Any]) -> str:
    """
    Генерирует описание/аннотацию книги.
    
    Args:
        transcript: Текст транскрипции
        title: Заголовок книги
        config: Конфигурация книги
        
    Returns:
        Сгенерированное описание
    """
    book_type = config.get('book', {}).get('type', 'scientific')
    audience = config.get('book', {}).get('target_audience', 'students')
    language = config.get('book', {}).get('language', 'ru')
    
    prompt = f"""
Создайте профессиональное описание (аннотацию) для книги с заголовком "{title}".
Тип книги: {book_type}
Целевая аудитория: {audience}
Язык: {language}

Описание должно быть:
- Длиной 150-200 слов
- Информативным и привлекательным
- Объясняющим, что читатель узнает из книги
- Подчёркивающим практическую ценность

Основано на следующем материале:
{transcript[:3000]}...

Верните ТОЛЬКО описание, без заголовка и дополнительных комментариев.
"""
    
    logger.info("Генерация описания книги...")
    description = _call_ai_model(prompt, config).strip()
    logger.info(f"Сгенерировано описание (длина: {len(description)} символов)")
    return description


def _generate_outline(transcript: str, title: str, config: Dict[str, Any]) -> List[str]:
    """
    Генерирует оглавление (структуру глав) книги.
    
    Args:
        transcript: Текст транскрипции
        title: Заголовок книги
        config: Конфигурация книги
        
    Returns:
        Список названий глав
    """
    book_type = config.get('book', {}).get('type', 'scientific')
    language = config.get('book', {}).get('language', 'ru')
    
    prompt = f"""
Создайте структуру (оглавление) для книги "{title}".
Тип книги: {book_type}
Язык: {language}

Структура должна включать 5-8 глав.
Каждая глава должна иметь ёмкое и информативное название.

Основано на следующем материале:
{transcript[:3000]}...

Верните ТОЛЬКО список названий глав, по одному на строку, в формате:
Глава 1: Название первой главы
Глава 2: Название второй главы
...и так далее
"""
    
    logger.info("Генерация оглавления книги...")
    outline_text = _call_ai_model(prompt, config).strip()
    
    # Парсинг оглавления
    chapters = []
    for line in outline_text.split('\n'):
        line = line.strip()
        if line and ('глава' in line.lower() or 'chapter' in line.lower()):
            # Извлекаем название главы после двоеточия или номера
            if ':' in line:
                chapter_title = line.split(':', 1)[1].strip()
            else:
                chapter_title = line
            chapters.append(chapter_title)
    
    logger.info(f"Сгенерировано оглавление с {len(chapters)} главами")
    return chapters


def _generate_chapter_content(
    chapter_title: str,
    chapter_num: int,
    total_chapters: int,
    transcript: str,
    outline: List[str],
    config: Dict[str, Any]
) -> str:
    """
    Генерирует содержимое одной главы.
    
    Args:
        chapter_title: Название главы
        chapter_num: Номер главы (1-based)
        total_chapters: Общее количество глав
        transcript: Исходная транскрипция
        outline: Полное оглавление
        config: Конфигурация книги
        
    Returns:
        Текст главы
    """
    book_type = config.get('book', {}).get('type', 'scientific')
    language = config.get('book', {}).get('language', 'ru')
    
    outline_text = '\n'.join([f"{i+1}. {title}" for i, title in enumerate(outline)])
    
    prompt = f"""
Напишите содержимое для главы {chapter_num} из {total_chapters}.
Название главы: "{chapter_title}"
Тип книги: {book_type}
Язык: {language}

Полная структура книги:
{outline_text}

Требования к главе:
- Объём: 1500-2500 слов
- Стиль: профессиональный, понятный для целевой аудитории
- Структура: введение, основные разделы, заключение/выводы
- Используйте примеры и иллюстрации концепций
- Логически связывайте с предыдущими и следующими главами

Основано на следующем исходном материале:
{transcript[:4000]}...

Напишите полный текст главы:
"""
    
    logger.info(f"Генерация главы {chapter_num}: {chapter_title}")
    chapter_content = _call_ai_model(prompt, config).strip()
    logger.info(f"Сгенерирована глава {chapter_num} (длина: {len(chapter_content)} символов)")
    return chapter_content


def generate_content_from_transcript(
    transcript: str,
    config_path: str
) -> Dict[str, Any]:
    """
    Основная функция для генерации полного содержимого книги.
    
    Генерирует:
    - Заголовок книги
    - Описание/аннотацию
    - Оглавление (структуру глав)
    - Содержимое каждой главы
    
    Args:
        transcript: Текст транскрипции, идей или исходных материалов
        config_path: Путь к файлу конфигурации book_config.yaml
        
    Returns:
        Словарь со структурой:
        {
            'title': str,
            'description': str,
            'outline': List[str],
            'chapters': [
                {'title': str, 'content': str},
                ...
            ]
        }
        
    Raises:
        ValueError: При некорректных параметрах
        Exception: При ошибках генерации
    """
    try:
        logger.info("=" * 60)
        logger.info("Начало генерации контента книги")
        logger.info("=" * 60)
        
        # Валидация входных данных
        if not transcript or len(transcript.strip()) < 100:
            raise ValueError("Транскрипция слишком короткая (минимум 100 символов)")
        
        # Загрузка конфигурации
        config = load_config(config_path)
        
        # Анализ ключевых тем (опционально, для будущего использования)
        themes = _extract_key_themes(transcript)
        logger.info(f"Ключевые темы: {', '.join(themes)}")
        
        # Генерация заголовка
        title = _generate_title(transcript, config)
        
        # Генерация описания
        description = _generate_description(transcript, title, config)
        
        # Генерация оглавления
        outline = _generate_outline(transcript, title, config)
        
        # Генерация глав
        chapters = []
        for i, chapter_title in enumerate(outline):
            chapter_content = _generate_chapter_content(
                chapter_title=chapter_title,
                chapter_num=i + 1,
                total_chapters=len(outline),
                transcript=transcript,
                outline=outline,
                config=config
            )
            
            chapters.append({
                'title': chapter_title,
                'content': chapter_content
            })
        
        result = {
            'title': title,
            'description': description,
            'outline': outline,
            'chapters': chapters,
            'metadata': {
                'book_type': config.get('book', {}).get('type'),
                'language': config.get('book', {}).get('language'),
                'target_audience': config.get('book', {}).get('target_audience'),
                'themes': themes
            }
        }
        
        logger.info("=" * 60)
        logger.info(f"Генерация контента завершена успешно")
        logger.info(f"Заголовок: {title}")
        logger.info(f"Количество глав: {len(chapters)}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при генерации контента: {e}", exc_info=True)
        raise


# Вспомогательные функции для совместимости с предыдущим API
def generate_title(transcript: str, config: Dict[str, Any]) -> str:
    """
    Устаревшая функция. Используйте generate_content_from_transcript.
    """
    logger.warning("generate_title() устарела. Используйте generate_content_from_transcript()")
    return _generate_title(transcript, config)


def generate_content(transcript: str, config: Dict[str, Any]) -> str:
    """
    Устаревшая функция. Используйте generate_content_from_transcript.
    """
    logger.warning("generate_content() устарела. Используйте generate_content_from_transcript()")
    # Возвращаем простое содержимое для обратной совместимости
    return "Generated Content (используйте generate_content_from_transcript для полной генерации)"
