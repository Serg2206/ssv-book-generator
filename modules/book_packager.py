"""
Модуль для упаковки финального продукта книги.

Создаёт структурированный пакет, содержащий:
- Финальный файл книги (PDF/EPUB)
- Артефакты (исходные данные, изображения, метаданные)
- README с описанием содержимого
- Метаинформация в формате JSON
"""

import logging
import os
import yaml
import json
import shutil
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)


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


def _create_package_directory(base_output_folder: str, book_title: str) -> Path:
    """
    Создаёт уникальную директорию для пакета книги.
    
    Args:
        base_output_folder: Базовая папка для выходных файлов
        book_title: Заголовок книги
        
    Returns:
        Path объект созданной директории
    """
    # Создаём безопасное имя директории
    safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')[:50]
    
    # Добавляем timestamp для уникальности
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{safe_title}_{timestamp}"
    
    package_path = Path(base_output_folder) / package_name
    package_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Создана директория пакета: {package_path}")
    return package_path


def _copy_book_file(book_file_path: str, package_dir: Path, new_name: Optional[str] = None) -> str:
    """
    Копирует финальный файл книги в пакет.
    
    Args:
        book_file_path: Путь к файлу книги
        package_dir: Директория пакета
        new_name: Новое имя файла (опционально)
        
    Returns:
        Путь к скопированному файлу
    """
    try:
        book_file = Path(book_file_path)
        
        if not book_file.exists():
            raise FileNotFoundError(f"Файл книги не найден: {book_file_path}")
        
        # Определяем имя файла
        if new_name:
            destination = package_dir / new_name
        else:
            destination = package_dir / book_file.name
        
        # Копируем файл
        shutil.copy2(book_file, destination)
        logger.debug(f"Файл книги скопирован: {destination}")
        
        return str(destination)
        
    except Exception as e:
        logger.error(f"Ошибка копирования файла книги: {e}")
        raise


def _save_artifacts(
    content_dict: Dict[str, Any],
    package_dir: Path
) -> Path:
    """
    Сохраняет артефакты генерации (контент, метаданные).
    
    Args:
        content_dict: Словарь с сгенерированным контентом
        package_dir: Директория пакета
        
    Returns:
        Path к директории артефактов
    """
    try:
        artifacts_dir = package_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Сохраняем полный контент в JSON
        content_file = artifacts_dir / "content.json"
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content_dict, f, ensure_ascii=False, indent=2)
        logger.debug(f"Контент сохранён: {content_file}")
        
        # Сохраняем только текст глав в отдельные файлы
        chapters_dir = artifacts_dir / "chapters"
        chapters_dir.mkdir(exist_ok=True)
        
        for i, chapter in enumerate(content_dict.get('chapters', [])):
            chapter_file = chapters_dir / f"chapter_{i+1:02d}.txt"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"Глава {i+1}: {chapter.get('title', '')}\n\n")
                f.write(chapter.get('content', ''))
            logger.debug(f"Глава {i+1} сохранена: {chapter_file}")
        
        logger.info(f"Артефакты сохранены в: {artifacts_dir}")
        return artifacts_dir
        
    except Exception as e:
        logger.error(f"Ошибка сохранения артефактов: {e}")
        raise


def _copy_illustrations(
    illustrations_paths: List[str],
    package_dir: Path
) -> List[str]:
    """
    Копирует иллюстрации в пакет.
    
    Args:
        illustrations_paths: Список путей к иллюстрациям
        package_dir: Директория пакета
        
    Returns:
        Список путей к скопированным иллюстрациям
    """
    try:
        if not illustrations_paths:
            logger.info("Нет иллюстраций для копирования")
            return []
        
        images_dir = package_dir / "artifacts" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        copied_paths = []
        
        for i, img_path in enumerate(illustrations_paths):
            if os.path.exists(img_path):
                img_file = Path(img_path)
                destination = images_dir / f"illustration_{i+1:02d}{img_file.suffix}"
                shutil.copy2(img_file, destination)
                copied_paths.append(str(destination))
                logger.debug(f"Иллюстрация {i+1} скопирована: {destination}")
            else:
                logger.warning(f"Иллюстрация не найдена: {img_path}")
        
        logger.info(f"Скопировано иллюстраций: {len(copied_paths)}")
        return copied_paths
        
    except Exception as e:
        logger.error(f"Ошибка копирования иллюстраций: {e}")
        raise


def _copy_cover(cover_path: str, package_dir: Path) -> Optional[str]:
    """
    Копирует обложку в пакет.
    
    Args:
        cover_path: Путь к обложке
        package_dir: Директория пакета
        
    Returns:
        Путь к скопированной обложке или None
    """
    try:
        if not cover_path or not os.path.exists(cover_path):
            logger.warning("Обложка не найдена")
            return None
        
        artifacts_dir = package_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        cover_file = Path(cover_path)
        destination = artifacts_dir / f"cover{cover_file.suffix}"
        shutil.copy2(cover_file, destination)
        
        logger.debug(f"Обложка скопирована: {destination}")
        return str(destination)
        
    except Exception as e:
        logger.error(f"Ошибка копирования обложки: {e}")
        return None


def _save_config(config_path: str, package_dir: Path) -> str:
    """
    Копирует файл конфигурации в пакет.
    
    Args:
        config_path: Путь к файлу конфигурации
        package_dir: Директория пакета
        
    Returns:
        Путь к скопированному файлу конфигурации
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Файл конфигурации не найден: {config_path}")
            return ""
        
        artifacts_dir = package_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        destination = artifacts_dir / "book_config.yaml"
        shutil.copy2(config_file, destination)
        
        logger.debug(f"Конфигурация скопирована: {destination}")
        return str(destination)
        
    except Exception as e:
        logger.error(f"Ошибка копирования конфигурации: {e}")
        return ""


def _generate_package_readme(
    content_dict: Dict[str, Any],
    config: Dict[str, Any],
    package_dir: Path,
    book_file_name: str
) -> str:
    """
    Генерирует README.md для пакета книги.
    
    Args:
        content_dict: Словарь с контентом книги
        config: Конфигурация
        package_dir: Директория пакета
        book_file_name: Имя файла книги
        
    Returns:
        Путь к созданному README
    """
    try:
        title = content_dict.get('title', 'Untitled')
        description = content_dict.get('description', '')
        chapters = content_dict.get('chapters', [])
        metadata = content_dict.get('metadata', {})
        
        # Информация о проекте
        project_name = config.get('project', {}).get('name', 'SSVproff Book Generator')
        project_version = config.get('project', {}).get('version', '1.0.0')
        
        # Создаём содержимое README
        readme_content = f"""# {title}

## Информация о книге

**Описание:**
{description}

**Метаданные:**
- Тип книги: {metadata.get('book_type', 'N/A')}
- Язык: {metadata.get('language', 'N/A')}
- Целевая аудитория: {metadata.get('target_audience', 'N/A')}
- Количество глав: {len(chapters)}
- Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Структура пакета

```
{package_dir.name}/
├── {book_file_name}                 # Финальный файл книги
├── README.md                        # Этот файл
└── artifacts/                       # Артефакты генерации
    ├── content.json                 # Полный контент в JSON
    ├── book_config.yaml             # Конфигурация генерации
    ├── cover.png                    # Обложка книги
    ├── chapters/                    # Главы в текстовом формате
    │   ├── chapter_01.txt
    │   ├── chapter_02.txt
    │   └── ...
    └── images/                      # Иллюстрации
        ├── illustration_01.png
        ├── illustration_02.png
        └── ...
```

## Оглавление

"""
        
        # Добавляем оглавление
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'Глава {i+1}')
            readme_content += f"{i+1}. {chapter_title}\n"
        
        readme_content += f"""

## О генераторе

Эта книга была создана с помощью **{project_name}** версии {project_version}.

**SSVproff** - профессиональный бренд для создания научных и образовательных материалов.

### Ключевые темы

"""
        
        # Добавляем ключевые темы
        themes = metadata.get('themes', [])
        if themes:
            for theme in themes:
                readme_content += f"- {theme}\n"
        else:
            readme_content += "- (не определено)\n"
        
        readme_content += """

## Использование

### Чтение книги
Откройте файл книги в соответствующем ридере:
- PDF: любой PDF-ридер (Adobe Reader, Foxit, встроенные просмотрщики)
- EPUB: электронные книги ридеры (Calibre, FBReader, Apple Books)

### Артефакты
Директория `artifacts/` содержит все исходные материалы и промежуточные данные,
использованные при создании книги. Это соответствует принципам Open Science
и позволяет воспроизводить результаты.

## Лицензия и авторские права

Контент создан при помощи ИИ-технологий и профессиональных инструментов SSVproff.

## Контакты

- Сайт: https://ssvproff.com
- GitHub: https://github.com/Serg2206/ssv-book-generator

---

*Создано с ❤️ с помощью SSVproff Book Generator*
"""
        
        # Сохраняем README
        readme_path = package_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"README создан: {readme_path}")
        return str(readme_path)
        
    except Exception as e:
        logger.error(f"Ошибка создания README: {e}")
        raise


def _generate_metadata_json(
    content_dict: Dict[str, Any],
    config: Dict[str, Any],
    package_dir: Path,
    book_file_path: str
) -> str:
    """
    Генерирует файл метаданных в JSON формате.
    
    Args:
        content_dict: Словарь с контентом книги
        config: Конфигурация
        package_dir: Директория пакета
        book_file_path: Путь к файлу книги
        
    Returns:
        Путь к файлу метаданных
    """
    try:
        metadata = {
            'package_info': {
                'package_name': package_dir.name,
                'creation_date': datetime.now().isoformat(),
                'generator': {
                    'name': config.get('project', {}).get('name', 'SSVproff Book Generator'),
                    'version': config.get('project', {}).get('version', '1.0.0')
                }
            },
            'book_info': {
                'title': content_dict.get('title', 'Untitled'),
                'description': content_dict.get('description', ''),
                'type': content_dict.get('metadata', {}).get('book_type', 'unknown'),
                'language': content_dict.get('metadata', {}).get('language', 'ru'),
                'target_audience': content_dict.get('metadata', {}).get('target_audience', 'general'),
                'chapters_count': len(content_dict.get('chapters', [])),
                'themes': content_dict.get('metadata', {}).get('themes', [])
            },
            'files': {
                'main_book': Path(book_file_path).name,
                'format': Path(book_file_path).suffix[1:],
                'readme': 'README.md',
                'content_json': 'artifacts/content.json',
                'config': 'artifacts/book_config.yaml'
            },
            'generation_config': {
                'ai_provider': config.get('ai', {}).get('content_provider', 'unknown'),
                'ai_model': config.get('ai', {}).get('content_model', 'unknown'),
                'image_provider': config.get('ai', {}).get('image_provider', 'unknown'),
                'output_format': config.get('formatting', {}).get('output_format', 'unknown'),
                'template': config.get('formatting', {}).get('template', 'default')
            }
        }
        
        metadata_path = package_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Метаданные созданы: {metadata_path}")
        return str(metadata_path)
        
    except Exception as e:
        logger.error(f"Ошибка создания метаданных: {e}")
        raise


def create_package(
    formatted_book_path: str,
    content_dict: Dict[str, Any],
    illustrations_paths: List[str],
    config_path: str,
    output_filename: Optional[str] = None,
    cover_path: Optional[str] = None
) -> str:
    """
    Создаёт полный пакет книги с артефактами и документацией.
    
    Args:
        formatted_book_path: Путь к отформатированному файлу книги
        content_dict: Словарь с контентом книги (из ai_content_generator)
        illustrations_paths: Список путей к иллюстрациям
        config_path: Путь к файлу конфигурации
        output_filename: Желаемое имя выходного файла (опционально)
        cover_path: Путь к обложке (опционально)
        
    Returns:
        Путь к директории пакета
        
    Raises:
        FileNotFoundError: Если файл книги не найден
        Exception: При ошибках упаковки
    """
    try:
        logger.info("=" * 60)
        logger.info("Начало упаковки книги")
        logger.info("=" * 60)
        
        # Загрузка конфигурации
        config = _load_config(config_path)
        
        # Проверка существования файла книги
        if not os.path.exists(formatted_book_path):
            raise FileNotFoundError(f"Файл книги не найден: {formatted_book_path}")
        
        title = content_dict.get('title', 'Untitled')
        logger.info(f"Упаковка книги: {title}")
        
        # Создание директории пакета
        base_output_folder = config.get('paths', {}).get('output_folder', './output')
        package_dir = _create_package_directory(base_output_folder, title)
        
        # Определение имени файла книги
        if output_filename:
            book_filename = output_filename
        else:
            book_filename = Path(formatted_book_path).name
        
        # Копирование основного файла книги
        logger.info("Копирование файла книги...")
        book_in_package = _copy_book_file(formatted_book_path, package_dir, book_filename)
        
        # Сохранение артефактов, если включено
        generate_artifacts = config.get('open_science', {}).get('generate_artifacts', True)
        
        if generate_artifacts:
            logger.info("Сохранение артефактов...")
            
            # Сохранение контента
            _save_artifacts(content_dict, package_dir)
            
            # Копирование иллюстраций
            _copy_illustrations(illustrations_paths, package_dir)
            
            # Копирование обложки
            if cover_path:
                _copy_cover(cover_path, package_dir)
            
            # Копирование конфигурации
            _save_config(config_path, package_dir)
            
            logger.info("Артефакты сохранены")
        else:
            logger.info("Сохранение артефактов отключено в конфигурации")
        
        # Генерация README, если включено
        generate_readme = config.get('open_science', {}).get('generate_readme', True)
        
        if generate_readme:
            logger.info("Генерация README...")
            _generate_package_readme(content_dict, config, package_dir, book_filename)
        
        # Генерация файла метаданных
        logger.info("Генерация метаданных...")
        _generate_metadata_json(content_dict, config, package_dir, book_in_package)
        
        logger.info("=" * 60)
        logger.info(f"Упаковка завершена успешно")
        logger.info(f"Пакет сохранён в: {package_dir}")
        logger.info("=" * 60)
        
        return str(package_dir)
        
    except Exception as e:
        logger.error(f"Ошибка при упаковке книги: {e}", exc_info=True)
        raise


# Устаревшая функция для обратной совместимости
def create_package_legacy(formatted_content, config, output_filename):
    """
    Устаревшая функция. Используйте create_package.
    """
    logger.warning("create_package_legacy() устарела. Используйте create_package()")
    package_path = f"output/{output_filename}"
    print(f"Book packaged to {package_path} (используйте create_package)")
    return package_path
