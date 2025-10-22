"""
Модуль для форматирования книг в различные форматы (PDF, EPUB).

Поддерживаемые форматы:
- PDF (с использованием fpdf2 или weasyprint)
- EPUB (с использованием ebooklib)
- HTML (базовая поддержка)
"""

import logging
import os
import yaml
import uuid
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

# Попытка импорта библиотек для форматирования
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    logger.warning("FPDF2 library not available. Install with: pip install fpdf2")

try:
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logger.warning("EbookLib not available. Install with: pip install ebooklib")

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
    output_dir = Path(base_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Директория для выходных файлов: {output_dir}")
    return output_dir


def _generate_unique_filename(base_name: str, extension: str) -> str:
    """
    Генерирует уникальное имя файла.
    
    Args:
        base_name: Базовое имя файла
        extension: Расширение файла (без точки)
        
    Returns:
        Уникальное имя файла
    """
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')[:50]  # Ограничиваем длину
    return f"{safe_name}_{timestamp}_{unique_id}.{extension}"


class SSVproffPDF(FPDF):
    """
    Кастомизированный класс PDF для брендирования SSVproff.
    """
    
    def __init__(self, title: str = "", author: str = "SSVproff"):
        super().__init__()
        self.book_title = title
        self.book_author = author
        
    def header(self):
        """Добавляет хедер на каждую страницу."""
        if self.page_no() > 1:  # Пропускаем хедер на первой странице (обложка)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, self.book_title[:50], 0, 0, 'L')
            self.ln(15)
    
    def footer(self):
        """Добавляет футер с номером страницы."""
        if self.page_no() > 1:  # Пропускаем футер на первой странице
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Страница {self.page_no()-1}', 0, 0, 'C')


def _format_to_pdf(
    content_dict: Dict[str, Any],
    cover_path: str,
    illustrations_paths: List[str],
    config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Форматирует книгу в PDF формат.
    
    Args:
        content_dict: Словарь с контентом книги
        cover_path: Путь к файлу обложки
        illustrations_paths: Список путей к иллюстрациям
        config: Конфигурация
        output_path: Путь для сохранения PDF
        
    Returns:
        Путь к созданному PDF файлу
    """
    if not FPDF_AVAILABLE:
        raise ImportError("FPDF2 library not installed")
    
    try:
        logger.info("Создание PDF документа...")
        
        title = content_dict.get('title', 'Untitled')
        description = content_dict.get('description', '')
        chapters = content_dict.get('chapters', [])
        
        # Создаём PDF
        pdf = SSVproffPDF(title=title)
        pdf.set_title(title)
        pdf.set_author("SSVproff")
        pdf.set_creator("SSVproff Book Generator")
        
        # === ОБЛОЖКА ===
        if cover_path and os.path.exists(cover_path):
            logger.debug(f"Добавление обложки: {cover_path}")
            pdf.add_page()
            try:
                # Добавляем изображение обложки
                pdf.image(cover_path, x=10, y=10, w=190)
            except Exception as e:
                logger.warning(f"Не удалось добавить обложку: {e}")
                # Текстовая заглушка
                pdf.set_font('Arial', 'B', 24)
                pdf.cell(0, 100, '', 0, 1)
                pdf.cell(0, 10, title, 0, 1, 'C')
        else:
            # Создаём текстовую обложку
            pdf.add_page()
            pdf.set_font('Arial', 'B', 24)
            pdf.cell(0, 100, '', 0, 1)
            pdf.cell(0, 10, title, 0, 1, 'C')
        
        # === СТРАНИЦА С ОПИСАНИЕМ ===
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'О книге', 0, 1, 'L')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        
        # Многострочное описание
        for line in description.split('\n'):
            if line.strip():
                pdf.multi_cell(0, 8, line.strip())
                pdf.ln(2)
        
        # === ОГЛАВЛЕНИЕ ===
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Оглавление', 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 12)
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'Глава {i+1}')
            pdf.cell(0, 8, f"{i+1}. {chapter_title}", 0, 1, 'L')
        
        # === ГЛАВЫ ===
        for i, chapter in enumerate(chapters):
            logger.debug(f"Форматирование главы {i+1}/{len(chapters)}")
            
            pdf.add_page()
            
            # Заголовок главы
            pdf.set_font('Arial', 'B', 16)
            chapter_title = chapter.get('title', f'Глава {i+1}')
            pdf.cell(0, 10, f"Глава {i+1}: {chapter_title}", 0, 1, 'L')
            pdf.ln(5)
            
            # Содержимое главы
            pdf.set_font('Arial', '', 11)
            chapter_content = chapter.get('content', '')
            
            # Разбиваем текст на параграфы
            paragraphs = chapter_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Убираем лишние пробелы и переносы
                    clean_para = ' '.join(para.split())
                    pdf.multi_cell(0, 7, clean_para)
                    pdf.ln(3)
            
            # Добавляем иллюстрацию, если есть
            if i < len(illustrations_paths):
                illustration_path = illustrations_paths[i]
                if os.path.exists(illustration_path):
                    try:
                        pdf.ln(5)
                        pdf.image(illustration_path, x=30, y=None, w=150)
                        pdf.ln(5)
                    except Exception as e:
                        logger.warning(f"Не удалось добавить иллюстрацию {i+1}: {e}")
        
        # === ФИНАЛЬНАЯ СТРАНИЦА ===
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 100, '', 0, 1)
        pdf.cell(0, 10, 'Создано с помощью SSVproff Book Generator', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, 'https://ssvproff.com', 0, 1, 'C')
        
        # Сохраняем PDF
        pdf.output(str(output_path))
        logger.info(f"PDF успешно создан: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}", exc_info=True)
        raise


def _format_to_epub(
    content_dict: Dict[str, Any],
    cover_path: str,
    illustrations_paths: List[str],
    config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Форматирует книгу в EPUB формат.
    
    Args:
        content_dict: Словарь с контентом книги
        cover_path: Путь к файлу обложки
        illustrations_paths: Список путей к иллюстрациям
        config: Конфигурация
        output_path: Путь для сохранения EPUB
        
    Returns:
        Путь к созданному EPUB файлу
    """
    if not EPUB_AVAILABLE:
        raise ImportError("EbookLib library not installed")
    
    try:
        logger.info("Создание EPUB документа...")
        
        title = content_dict.get('title', 'Untitled')
        description = content_dict.get('description', '')
        chapters = content_dict.get('chapters', [])
        language = config.get('book', {}).get('language', 'ru')
        
        # Создаём EPUB книгу
        book = epub.EpubBook()
        
        # Метаданные
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(title)
        book.set_language(language)
        book.add_author('SSVproff')
        
        # Добавляем обложку
        if cover_path and os.path.exists(cover_path):
            logger.debug(f"Добавление обложки: {cover_path}")
            try:
                with open(cover_path, 'rb') as f:
                    cover_content = f.read()
                book.set_cover("cover.jpg", cover_content)
            except Exception as e:
                logger.warning(f"Не удалось добавить обложку: {e}")
        
        # CSS стиль
        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 2em;
        }
        h1 {
            color: #333;
            font-size: 2em;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        h2 {
            color: #555;
            font-size: 1.5em;
            margin-top: 1em;
        }
        p {
            text-align: justify;
            margin-bottom: 1em;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }
        .description {
            font-style: italic;
            margin: 2em 0;
        }
        '''
        
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # Страница с описанием
        intro_content = f'''
        <html>
        <head>
            <link rel="stylesheet" href="style/nav.css" type="text/css"/>
        </head>
        <body>
            <h1>О книге</h1>
            <div class="description">
                {description.replace(chr(10), '<br/>')}
            </div>
        </body>
        </html>
        '''
        
        intro = epub.EpubHtml(
            title='О книге',
            file_name='intro.xhtml',
            lang=language
        )
        intro.content = intro_content
        book.add_item(intro)
        
        # Добавляем главы
        epub_chapters = []
        
        for i, chapter in enumerate(chapters):
            logger.debug(f"Форматирование главы {i+1}/{len(chapters)}")
            
            chapter_title = chapter.get('title', f'Глава {i+1}')
            chapter_content = chapter.get('content', '')
            
            # Форматируем контент главы
            formatted_content = chapter_content.replace('\n\n', '</p><p>').replace('\n', '<br/>')
            
            # HTML контент главы
            chapter_html = f'''
            <html>
            <head>
                <link rel="stylesheet" href="style/nav.css" type="text/css"/>
            </head>
            <body>
                <h1>Глава {i+1}: {chapter_title}</h1>
                <p>{formatted_content}</p>
            </body>
            </html>
            '''
            
            epub_chapter = epub.EpubHtml(
                title=chapter_title,
                file_name=f'chapter_{i+1}.xhtml',
                lang=language
            )
            epub_chapter.content = chapter_html
            
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            
            # Добавляем иллюстрацию, если есть
            if i < len(illustrations_paths):
                illustration_path = illustrations_paths[i]
                if os.path.exists(illustration_path):
                    try:
                        with open(illustration_path, 'rb') as f:
                            img_content = f.read()
                        
                        img_name = f'images/illustration_{i+1}.jpg'
                        epub_image = epub.EpubItem(
                            uid=f"image_{i+1}",
                            file_name=img_name,
                            media_type="image/jpeg",
                            content=img_content
                        )
                        book.add_item(epub_image)
                    except Exception as e:
                        logger.warning(f"Не удалось добавить иллюстрацию {i+1}: {e}")
        
        # Оглавление
        book.toc = [intro] + epub_chapters
        
        # Навигация
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Spine (порядок страниц)
        book.spine = ['nav', intro] + epub_chapters
        
        # Сохраняем EPUB
        epub.write_epub(str(output_path), book, {})
        logger.info(f"EPUB успешно создан: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании EPUB: {e}", exc_info=True)
        raise


def _format_to_html(
    content_dict: Dict[str, Any],
    cover_path: str,
    illustrations_paths: List[str],
    config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Форматирует книгу в HTML формат.
    
    Args:
        content_dict: Словарь с контентом книги
        cover_path: Путь к файлу обложки
        illustrations_paths: Список путей к иллюстрациям
        config: Конфигурация
        output_path: Путь для сохранения HTML
        
    Returns:
        Путь к созданному HTML файлу
    """
    try:
        logger.info("Создание HTML документа...")
        
        title = content_dict.get('title', 'Untitled')
        description = content_dict.get('description', '')
        chapters = content_dict.get('chapters', [])
        
        # HTML шаблон
        html_content = f'''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .cover {{
            text-align: center;
            padding: 50px 0;
        }}
        .cover img {{
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
        }}
        .description {{
            background-color: #ecf0f1;
            padding: 20px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
            font-style: italic;
        }}
        .chapter {{
            background-color: white;
            padding: 30px;
            margin: 30px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chapter img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 4px;
        }}
        .toc {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .toc li {{
            padding: 5px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="cover">
        {"<img src='" + cover_path + "' alt='Cover'/>" if cover_path and os.path.exists(cover_path) else ""}
        <h1>{title}</h1>
    </div>
    
    <div class="description">
        {description.replace(chr(10), '<br/>')}
    </div>
    
    <div class="toc">
        <h2>Оглавление</h2>
        <ul>
'''
        
        # Оглавление
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'Глава {i+1}')
            html_content += f'            <li><a href="#chapter{i+1}">{i+1}. {chapter_title}</a></li>\n'
        
        html_content += '''        </ul>
    </div>
'''
        
        # Главы
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'Глава {i+1}')
            chapter_content = chapter.get('content', '')
            
            formatted_content = chapter_content.replace('\n\n', '</p><p>').replace('\n', '<br/>')
            
            html_content += f'''
    <div class="chapter" id="chapter{i+1}">
        <h2>Глава {i+1}: {chapter_title}</h2>
        <p>{formatted_content}</p>
'''
            
            # Иллюстрация
            if i < len(illustrations_paths):
                illustration_path = illustrations_paths[i]
                if os.path.exists(illustration_path):
                    html_content += f'        <img src="{illustration_path}" alt="Illustration {i+1}"/>\n'
            
            html_content += '    </div>\n'
        
        # Футер
        html_content += '''
    <div class="footer">
        <p>Создано с помощью SSVproff Book Generator</p>
        <p><a href="https://ssvproff.com">https://ssvproff.com</a></p>
    </div>
</body>
</html>
'''
        
        # Сохраняем HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML успешно создан: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании HTML: {e}", exc_info=True)
        raise


def format_to_format_type(
    content_dict: Dict[str, Any],
    cover_path: str,
    illustrations_paths: List[str],
    config_path: str
) -> str:
    """
    Основная функция для форматирования книги в заданный формат.
    
    Args:
        content_dict: Словарь с контентом книги (из ai_content_generator)
        cover_path: Путь к файлу обложки
        illustrations_paths: Список путей к иллюстрациям
        config_path: Путь к файлу конфигурации
        
    Returns:
        Путь к отформатированному файлу книги
        
    Raises:
        ValueError: При неподдерживаемом формате
        Exception: При ошибках форматирования
    """
    try:
        logger.info("=" * 60)
        logger.info("Начало форматирования книги")
        logger.info("=" * 60)
        
        # Загрузка конфигурации
        config = _load_config(config_path)
        
        # Определение формата вывода
        output_format = config.get('formatting', {}).get('output_format', 'pdf').lower()
        title = content_dict.get('title', 'Untitled')
        
        logger.info(f"Формат вывода: {output_format}")
        logger.info(f"Заголовок книги: {title}")
        
        # Подготовка выходной директории
        output_dir = _ensure_output_dir(config.get('paths', {}).get('output_folder', './output'))
        
        # Генерация имени файла
        output_filename = _generate_unique_filename(title, output_format)
        output_path = output_dir / output_filename
        
        # Форматирование в зависимости от типа
        if output_format == 'pdf':
            result_path = _format_to_pdf(content_dict, cover_path, illustrations_paths, config, output_path)
        elif output_format == 'epub':
            result_path = _format_to_epub(content_dict, cover_path, illustrations_paths, config, output_path)
        elif output_format == 'html':
            result_path = _format_to_html(content_dict, cover_path, illustrations_paths, config, output_path)
        else:
            raise ValueError(f"Неподдерживаемый формат вывода: {output_format}")
        
        logger.info("=" * 60)
        logger.info(f"Форматирование завершено успешно")
        logger.info(f"Файл книги: {result_path}")
        logger.info("=" * 60)
        
        return result_path
        
    except Exception as e:
        logger.error(f"Ошибка при форматировании книги: {e}", exc_info=True)
        raise


# Устаревшая функция для обратной совместимости
def apply_formatting(content, cover_path, illustrations, config):
    """
    Устаревшая функция. Используйте format_to_format_type.
    """
    logger.warning("apply_formatting() устарела. Используйте format_to_format_type()")
    return "Formatted Book Content (используйте format_to_format_type)"
