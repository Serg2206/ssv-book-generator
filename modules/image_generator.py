"""
Модуль для генерации обложек и иллюстраций книг с использованием ИИ API.

Поддерживает:
- OpenAI DALL-E для генерации изображений
- Stable Diffusion через различные API
- Заглушки для тестирования без API
"""

import logging
import os
import yaml
import requests
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
import time

# Настройка логирования
logger = logging.getLogger(__name__)

# Попытка импорта библиотек для генерации изображений
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Install with: pip install openai")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow library not available. Install with: pip install Pillow")


def _load_config(config_path: str) -> Dict[str, Any]:
    """
    Загружает конфигурационный файл YAML.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Словарь с конфигурацией
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        raise


def _ensure_output_dir(base_path: str = "./output") -> Path:
    """
    Создаёт директорию для выходных файлов, если её нет.
    
    Args:
        base_path: Базовый путь для выходных файлов
        
    Returns:
        Path объект директории
    """
    output_dir = Path(base_path) / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Директория для изображений: {output_dir}")
    return output_dir


def _generate_unique_filename(prefix: str, extension: str = "png") -> str:
    """
    Генерирует уникальное имя файла.
    
    Args:
        prefix: Префикс имени файла
        extension: Расширение файла
        
    Returns:
        Уникальное имя файла
    """
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"


def _call_openai_dalle(prompt: str, config: Dict[str, Any], output_path: Path) -> str:
    """
    Генерирует изображение с использованием OpenAI DALL-E.
    
    Args:
        prompt: Текстовое описание изображения
        config: Конфигурация с параметрами API
        output_path: Путь для сохранения изображения
        
    Returns:
        Путь к сохранённому файлу
        
    Raises:
        Exception: При ошибках API
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI library not installed")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")
        
        client = openai.OpenAI(api_key=api_key)
        
        model = config.get('ai', {}).get('image_model', 'dall-e-3')
        
        logger.info(f"Генерация изображения через DALL-E: {model}")
        logger.debug(f"Промпт: {prompt[:100]}...")
        
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Получаем URL изображения
        image_url = response.data[0].url
        
        # Скачиваем изображение
        logger.debug(f"Скачивание изображения с {image_url}")
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        # Сохраняем файл
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        
        logger.info(f"Изображение сохранено: {output_path}")
        return str(output_path)
        
    except openai.APIError as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при генерации изображения: {e}")
        raise


def _call_stability_ai(prompt: str, config: Dict[str, Any], output_path: Path) -> str:
    """
    Генерирует изображение с использованием Stability AI (Stable Diffusion).
    
    Args:
        prompt: Текстовое описание изображения
        config: Конфигурация с параметрами API
        output_path: Путь для сохранения изображения
        
    Returns:
        Путь к сохранённому файлу
        
    Raises:
        Exception: При ошибках API
    """
    try:
        api_key = os.getenv('STABILITY_API_KEY')
        if not api_key:
            raise ValueError("STABILITY_API_KEY не установлен в переменных окружения")
        
        # API endpoint для Stability AI
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30
        }
        
        logger.info("Генерация изображения через Stability AI")
        logger.debug(f"Промпт: {prompt[:100]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Получаем base64 изображение из ответа
        import base64
        for artifact in data.get("artifacts", []):
            if artifact.get("finishReason") == "SUCCESS":
                image_data = base64.b64decode(artifact["base64"])
                
                # Сохраняем файл
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Изображение сохранено: {output_path}")
                return str(output_path)
        
        raise Exception("Не удалось получить изображение из ответа API")
        
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса к Stability AI: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при генерации изображения: {e}")
        raise


def _create_placeholder_image(output_path: Path, text: str = "Placeholder") -> str:
    """
    Создаёт заглушку-изображение для тестирования.
    
    Args:
        output_path: Путь для сохранения изображения
        text: Текст для отображения на изображении
        
    Returns:
        Путь к сохранённому файлу
    """
    if not PIL_AVAILABLE:
        # Создаём пустой файл если PIL недоступен
        output_path.touch()
        logger.warning(f"Создан пустой файл-заглушка: {output_path}")
        return str(output_path)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Создаём изображение 1024x1024
        img = Image.new('RGB', (1024, 1024), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Центрируем текст
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((1024 - text_width) // 2, (1024 - text_height) // 2)
        
        draw.text(position, text, fill=(100, 100, 100), font=font)
        
        # Сохраняем
        img.save(output_path)
        logger.info(f"Создано изображение-заглушка: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Ошибка создания заглушки: {e}")
        # Создаём пустой файл
        output_path.touch()
        return str(output_path)


def generate_cover(title: str, book_type: str, config_path: str) -> str:
    """
    Генерирует обложку книги на основе заголовка и типа.
    
    Args:
        title: Заголовок книги
        book_type: Тип книги (scientific, fiction, surgery, oncology)
        config_path: Путь к файлу конфигурации
        
    Returns:
        Путь к файлу обложки
        
    Raises:
        ValueError: При некорректных параметрах
        Exception: При ошибках генерации
    """
    try:
        logger.info("=" * 60)
        logger.info("Генерация обложки книги")
        logger.info(f"Заголовок: {title}")
        logger.info(f"Тип: {book_type}")
        logger.info("=" * 60)
        
        # Загрузка конфигурации
        config = _load_config(config_path)
        
        # Подготовка выходной директории
        output_dir = _ensure_output_dir(config.get('paths', {}).get('output_folder', './output'))
        filename = _generate_unique_filename("cover")
        output_path = output_dir / filename
        
        # Формирование промпта для генерации обложки
        branding_style = config.get('branding', {}).get('style', 'professional')
        language = config.get('book', {}).get('language', 'ru')
        
        # Описания стилей для разных типов книг
        style_descriptions = {
            'scientific': 'professional, academic, clean design with diagrams and scientific elements',
            'fiction': 'creative, artistic, imaginative design with narrative elements',
            'surgery': 'medical, professional, precise design with surgical instruments or anatomy',
            'oncology': 'medical, compassionate, professional design with cancer awareness elements'
        }
        
        style_desc = style_descriptions.get(book_type, 'professional and modern')
        
        prompt = f"""
Professional book cover design for a {book_type} book titled "{title}".
Style: {style_desc}, {branding_style} branding.
High quality, modern, {language} language context.
Include space for title text, clean layout, SSVproff brand style.
No text on the cover, just visual design.
"""
        
        logger.debug(f"Промпт для обложки: {prompt}")
        
        # Определение провайдера
        image_provider = config.get('ai', {}).get('image_provider', 'placeholder')
        
        # Генерация изображения
        if image_provider == 'openai_dalle':
            result_path = _call_openai_dalle(prompt, config, output_path)
        elif image_provider == 'stable_diffusion':
            result_path = _call_stability_ai(prompt, config, output_path)
        elif image_provider == 'placeholder':
            logger.warning("Использование заглушки вместо реальной генерации изображения")
            result_path = _create_placeholder_image(output_path, f"Cover\n{title}")
        else:
            logger.warning(f"Неизвестный провайдер '{image_provider}', используется заглушка")
            result_path = _create_placeholder_image(output_path, f"Cover\n{title}")
        
        logger.info(f"Обложка успешно создана: {result_path}")
        return result_path
        
    except Exception as e:
        logger.error(f"Ошибка при генерации обложки: {e}", exc_info=True)
        raise


def generate_illustrations(
    content_chunks: List[Dict[str, str]],
    config_path: str,
    max_illustrations: Optional[int] = None
) -> List[str]:
    """
    Генерирует иллюстрации для глав книги.
    
    Args:
        content_chunks: Список словарей с информацией о главах
                       Формат: [{'title': str, 'content': str}, ...]
        config_path: Путь к файлу конфигурации
        max_illustrations: Максимальное количество иллюстраций (опционально)
        
    Returns:
        Список путей к файлам иллюстраций
        
    Raises:
        ValueError: При некорректных параметрах
        Exception: При ошибках генерации
    """
    try:
        logger.info("=" * 60)
        logger.info("Генерация иллюстраций для книги")
        logger.info(f"Количество глав: {len(content_chunks)}")
        logger.info("=" * 60)
        
        if not content_chunks:
            logger.warning("Нет контента для генерации иллюстраций")
            return []
        
        # Загрузка конфигурации
        config = _load_config(config_path)
        
        # Подготовка выходной директории
        output_dir = _ensure_output_dir(config.get('paths', {}).get('output_folder', './output'))
        
        # Ограничение количества иллюстраций
        if max_illustrations:
            content_chunks = content_chunks[:max_illustrations]
        
        book_type = config.get('book', {}).get('type', 'scientific')
        language = config.get('book', {}).get('language', 'ru')
        
        illustration_paths = []
        
        for i, chunk in enumerate(content_chunks):
            try:
                chapter_title = chunk.get('title', f'Chapter {i+1}')
                chapter_content = chunk.get('content', '')
                
                logger.info(f"Генерация иллюстрации {i+1}/{len(content_chunks)}: {chapter_title}")
                
                # Извлечение ключевых концепций из контента (первые 500 символов)
                content_preview = chapter_content[:500] if chapter_content else chapter_title
                
                # Формирование промпта для иллюстрации
                prompt = f"""
Professional illustration for a {book_type} book chapter titled "{chapter_title}".
Visual representation of the chapter's key concepts.
Style: educational, clear, professional, suitable for {language} language audience.
High quality, modern, informative visual.
Context: {content_preview[:200]}
"""
                
                # Генерация имени файла
                filename = _generate_unique_filename(f"illustration_{i+1:02d}")
                output_path = output_dir / filename
                
                # Определение провайдера
                image_provider = config.get('ai', {}).get('image_provider', 'placeholder')
                
                # Генерация изображения
                if image_provider == 'openai_dalle':
                    result_path = _call_openai_dalle(prompt, config, output_path)
                elif image_provider == 'stable_diffusion':
                    result_path = _call_stability_ai(prompt, config, output_path)
                elif image_provider == 'placeholder':
                    result_path = _create_placeholder_image(output_path, f"Illustration {i+1}\n{chapter_title[:30]}")
                else:
                    result_path = _create_placeholder_image(output_path, f"Illustration {i+1}\n{chapter_title[:30]}")
                
                illustration_paths.append(result_path)
                
                # Небольшая задержка между запросами к API
                if image_provider in ['openai_dalle', 'stable_diffusion']:
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка при генерации иллюстрации {i+1}: {e}")
                # Создаём заглушку в случае ошибки
                filename = _generate_unique_filename(f"illustration_{i+1:02d}_error")
                output_path = output_dir / filename
                fallback_path = _create_placeholder_image(output_path, f"Error\nIllustration {i+1}")
                illustration_paths.append(fallback_path)
        
        logger.info("=" * 60)
        logger.info(f"Генерация иллюстраций завершена: {len(illustration_paths)} изображений")
        logger.info("=" * 60)
        
        return illustration_paths
        
    except Exception as e:
        logger.error(f"Критическая ошибка при генерации иллюстраций: {e}", exc_info=True)
        raise


# Вспомогательная функция для совместимости со старым API
def generate_cover_legacy(title: str, config: Dict[str, Any]) -> str:
    """
    Устаревшая функция. Используйте generate_cover с config_path.
    """
    logger.warning("generate_cover_legacy() устарела")
    # Создаём временный файл конфигурации или используем заглушку
    return "Generated Cover Path (legacy stub)"


def generate_illustrations_legacy(content: str, config: Dict[str, Any]) -> List[str]:
    """
    Устаревшая функция. Используйте generate_illustrations с content_chunks.
    """
    logger.warning("generate_illustrations_legacy() устарела")
    return ["Illustration Path 1 (legacy stub)", "Illustration Path 2 (legacy stub)"]
