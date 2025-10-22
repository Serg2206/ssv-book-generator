"""
SSVproff Book Generator - Главный модуль

Автоматическая генерация книг с использованием ИИ:
- Генерация контента через AI API
- Создание обложек и иллюстраций
- Форматирование в PDF/EPUB
- Упаковка с артефактами и документацией
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Импорт модулей генератора
from modules import ai_content_generator
from modules import image_generator
from modules import book_formatter
from modules import book_packager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('book_generator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def validate_input_file(input_file: str) -> str:
    """
    Проверяет существование и читаемость входного файла.
    
    Args:
        input_file: Путь к входному файлу
        
    Returns:
        Содержимое файла
        
    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если файл пустой или нечитаемый
    """
    try:
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Входной файл не найден: {input_file}")
        
        if not input_path.is_file():
            raise ValueError(f"Путь не является файлом: {input_file}")
        
        # Читаем содержимое
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content or len(content.strip()) < 100:
            raise ValueError("Входной файл слишком короткий (минимум 100 символов)")
        
        logger.info(f"Входной файл загружен: {input_file} ({len(content)} символов)")
        return content
        
    except Exception as e:
        logger.error(f"Ошибка при чтении входного файла: {e}")
        raise


def validate_config_file(config_file: str) -> None:
    """
    Проверяет существование файла конфигурации.
    
    Args:
        config_file: Путь к файлу конфигурации
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    try:
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {config_file}")
        
        if not config_path.is_file():
            raise ValueError(f"Путь не является файлом: {config_file}")
        
        logger.info(f"Файл конфигурации найден: {config_file}")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке файла конфигурации: {e}")
        raise


def create_output_directories(config_path: str) -> None:
    """
    Создаёт необходимые выходные директории.
    
    Args:
        config_path: Путь к файлу конфигурации
    """
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаём директории из конфигурации
        output_folder = config.get('paths', {}).get('output_folder', './output')
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        input_folder = config.get('paths', {}).get('input_folder', './input')
        Path(input_folder).mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Директории созданы: {output_folder}, {input_folder}")
        
    except Exception as e:
        logger.warning(f"Не удалось создать директории: {e}")


def generate_book(input_file: str, config_file: str) -> Optional[str]:
    """
    Основная функция генерации книги.
    
    Args:
        input_file: Путь к входному файлу с идеями/транскрипцией
        config_file: Путь к файлу конфигурации
        
    Returns:
        Путь к финальному пакету книги или None при ошибке
        
    Raises:
        Exception: При критических ошибках генерации
    """
    package_path = None
    
    try:
        logger.info("=" * 80)
        logger.info("НАЧАЛО ГЕНЕРАЦИИ КНИГИ")
        logger.info("=" * 80)
        
        # Этап 1: Валидация входных данных
        logger.info("\n[ЭТАП 1/5] Валидация входных данных")
        logger.info("-" * 80)
        
        validate_config_file(config_file)
        input_content = validate_input_file(input_file)
        create_output_directories(config_file)
        
        logger.info("✓ Валидация завершена успешно")
        
        # Этап 2: Генерация контента
        logger.info("\n[ЭТАП 2/5] Генерация контента через ИИ")
        logger.info("-" * 80)
        
        content_result = ai_content_generator.generate_content_from_transcript(
            transcript=input_content,
            config_path=config_file
        )
        
        logger.info(f"✓ Контент сгенерирован:")
        logger.info(f"  - Заголовок: {content_result.get('title', 'N/A')}")
        logger.info(f"  - Количество глав: {len(content_result.get('chapters', []))}")
        
        # Этап 3: Генерация изображений
        logger.info("\n[ЭТАП 3/5] Генерация обложки и иллюстраций")
        logger.info("-" * 80)
        
        # Загружаем конфигурацию для получения типа книги
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        book_type = config.get('book', {}).get('type', 'scientific')
        
        # Генерация обложки
        cover_path = image_generator.generate_cover(
            title=content_result['title'],
            book_type=book_type,
            config_path=config_file
        )
        
        logger.info(f"✓ Обложка создана: {cover_path}")
        
        # Генерация иллюстраций
        illustrations_paths = image_generator.generate_illustrations(
            content_chunks=content_result['chapters'],
            config_path=config_file,
            max_illustrations=5  # Ограничиваем для экономии
        )
        
        logger.info(f"✓ Иллюстрации созданы: {len(illustrations_paths)} изображений")
        
        # Этап 4: Форматирование книги
        logger.info("\n[ЭТАП 4/5] Форматирование книги")
        logger.info("-" * 80)
        
        formatted_book_path = book_formatter.format_to_format_type(
            content_dict=content_result,
            cover_path=cover_path,
            illustrations_paths=illustrations_paths,
            config_path=config_file
        )
        
        logger.info(f"✓ Книга отформатирована: {formatted_book_path}")
        
        # Этап 5: Упаковка результата
        logger.info("\n[ЭТАП 5/5] Упаковка финального продукта")
        logger.info("-" * 80)
        
        package_path = book_packager.create_package(
            formatted_book_path=formatted_book_path,
            content_dict=content_result,
            illustrations_paths=illustrations_paths,
            config_path=config_file,
            cover_path=cover_path
        )
        
        logger.info(f"✓ Пакет создан: {package_path}")
        
        # Финальный отчёт
        logger.info("\n" + "=" * 80)
        logger.info("ГЕНЕРАЦИЯ КНИГИ ЗАВЕРШЕНА УСПЕШНО! 🎉")
        logger.info("=" * 80)
        logger.info(f"\nФинальный пакет:")
        logger.info(f"  📦 {package_path}")
        logger.info(f"\nСодержимое пакета:")
        logger.info(f"  📘 Книга: {content_result['title']}")
        logger.info(f"  📄 Формат: {config.get('formatting', {}).get('output_format', 'N/A').upper()}")
        logger.info(f"  📝 Глав: {len(content_result['chapters'])}")
        logger.info(f"  🖼️  Иллюстраций: {len(illustrations_paths)}")
        logger.info(f"\nДополнительно:")
        logger.info(f"  • README.md с описанием")
        logger.info(f"  • Артефакты генерации (если включено)")
        logger.info(f"  • Метаданные в JSON")
        logger.info("\n" + "=" * 80)
        
        return package_path
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Генерация прервана пользователем")
        return None
        
    except Exception as e:
        logger.error("\n\n❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ГЕНЕРАЦИИ КНИГИ")
        logger.error(f"Ошибка: {e}", exc_info=True)
        logger.error("\nПроверьте:")
        logger.error("  1. API ключи в переменных окружения (OPENAI_API_KEY, etc.)")
        logger.error("  2. Корректность файла конфигурации")
        logger.error("  3. Наличие необходимых зависимостей (см. requirements.txt)")
        logger.error("  4. Логи выше для деталей ошибки")
        return None


def main():
    """
    Точка входа в программу.
    """
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description='SSVproff Book Generator v1.0 - Автоматическая генерация книг с помощью ИИ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  
  Базовое использование:
    python main.py --input_file input/ideas.txt
  
  С кастомной конфигурацией:
    python main.py --input_file input/transcript.txt --config my_config.yaml
  
  С включённым отладочным режимом:
    python main.py --input_file input/ideas.txt --verbose

Требования:
  - Входной файл должен содержать минимум 100 символов текста
  - API ключи должны быть установлены в переменных окружения
  - Файл конфигурации должен быть валидным YAML

Для подробной информации см. README.md
        """
    )
    
    parser.add_argument(
        '--input_file',
        type=str,
        required=True,
        help='Путь к входному файлу (.txt) с идеями или транскрипцией'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='book_config.yaml',
        help='Путь к файлу конфигурации (по умолчанию: book_config.yaml)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Включить подробный вывод (DEBUG уровень логирования)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='SSVproff Book Generator v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Включён режим подробного логирования")
    
    # Вывод заголовка
    print("\n" + "=" * 80)
    print("SSVproff Book Generator v1.0".center(80))
    print("Автоматическая генерация книг с помощью ИИ".center(80))
    print("=" * 80 + "\n")
    
    # Проверка переменных окружения
    api_keys_status = []
    
    if os.getenv('OPENAI_API_KEY'):
        api_keys_status.append("✓ OPENAI_API_KEY установлен")
    else:
        api_keys_status.append("⚠ OPENAI_API_KEY не установлен")
    
    if os.getenv('ANTHROPIC_API_KEY'):
        api_keys_status.append("✓ ANTHROPIC_API_KEY установлен")
    else:
        api_keys_status.append("⚠ ANTHROPIC_API_KEY не установлен")
    
    logger.info("Статус API ключей:")
    for status in api_keys_status:
        logger.info(f"  {status}")
    
    logger.info(f"\nПараметры запуска:")
    logger.info(f"  Входной файл: {args.input_file}")
    logger.info(f"  Конфигурация: {args.config}")
    logger.info(f"  Подробный режим: {args.verbose}")
    
    # Запуск генерации
    try:
        package_path = generate_book(args.input_file, args.config)
        
        if package_path:
            print("\n" + "=" * 80)
            print("УСПЕХ! Книга успешно сгенерирована! 🎉".center(80))
            print("=" * 80)
            print(f"\n📦 Пакет сохранён: {package_path}\n")
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("ОШИБКА: Генерация не завершена".center(80))
            print("=" * 80)
            print("\nСм. логи выше для деталей ошибки\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа прервана пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
