# SSVproff Book Generator

**Автоматизированный инструмент для генерации профессиональных книг** под брендом **"SSVproff"**.

[![License: MIT](https://i.ytimg.com/vi/4cgpu9L2AE8/maxresdefault.jpg)
[![Python 3.8+](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Blue_Python_3.8_Shield_Badge.svg/2560px-Blue_Python_3.8_Shield_Badge.svg.png)

## 🎯 Возможности

Генерирует:
- ✨ **Интеллектуальный контент** с помощью OpenAI GPT-4 / Anthropic Claude
- 🎨 **Обложки и иллюстрации** через DALL-E / Stable Diffusion
- 📚 **Форматированные книги** в форматах PDF, EPUB, HTML
- 📦 **Структурированные пакеты** с артефактами и метаданными
- 🔬 **Open Science workflow** для воспроизводимости результатов

Разработан **профессором С.В. Сушковым** для медицинского и научного сообщества.

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Установка](#-установка)
- [Быстрый старт](#-быстрый-старт)
- [Конфигурация](#-конфигурация)
- [Примеры использования](#-примеры-использования)
- [Архитектура](#-архитектура)
- [Разработка](#-разработка)
- [Тестирование](#-тестирование)
- [Вклад в развитие](#-вклад-в-развитие)
- [Лицензия](#-лицензия)

---

## 🚀 Установка

### Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Git

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/Serg2206/ssv-book-generator.git
cd ssv-book-generator
```

### Шаг 2: Создание виртуального окружения (рекомендуется)

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Шаг 3: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 4: Настройка API ключей

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваши API ключи:

```env
# OpenAI API (для GPT-4 и DALL-E)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API (опционально, для Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Stability AI (опционально, для Stable Diffusion)
STABILITY_API_KEY=your_stability_api_key_here
```

---

## ⚡ Быстрый старт

### 1. Подготовка входных данных

Создайте текстовый файл с идеями или транскрипцией в папке `input/`:

```bash
echo "Ваши идеи для книги..." > input/my_ideas.txt
```

Или используйте пример:
```bash
# Уже готов в input/sample_ideas.txt
```

### 2. Базовый запуск

```bash
python main.py --input_file input/sample_ideas.txt
```

### 3. С пользовательской конфигурацией

```bash
python main.py --input_file input/my_ideas.txt --config my_custom_config.yaml
```

### 4. Результаты

Финальный пакет будет создан в директории `output/` со следующей структурой:

```
output/
└── My_Book_Title_20241022_123456/
    ├── My_Book_Title.pdf          # Финальная книга
    ├── README.md                   # Описание пакета
    ├── metadata.json               # Метаданные генерации
    └── artifacts/                  # Артефакты (если включено)
        ├── content.json
        ├── book_config.yaml
        ├── cover.png
        ├── chapters/
        │   ├── chapter_01.txt
        │   └── ...
        └── images/
            ├── illustration_01.png
            └── ...
```

---

## ⚙️ Конфигурация

### Основной файл конфигурации: `book_config.yaml`

```yaml
# Информация о проекте
project:
  name: "SSVproff Book Generator"
  version: "1.0.0"

# Пути к директориям
paths:
  input_folder: "./input"
  output_folder: "./output"

# Настройки книги
book:
  title: "Моя книга"                # Будет перезаписан ИИ
  type: "scientific"                 # scientific, fiction, surgery, oncology
  target_audience: "students"        # doctors, students, patients, general_public
  language: "ru"                     # ru, en, etc.
  genre: "educational"               # educational, review, narrative, textbook

# Настройки ИИ
ai:
  content_provider: "openai_gpt"     # openai_gpt, anthropic_claude
  content_model: "gpt-4o"            # gpt-4o, claude-3-opus-20240229
  image_provider: "placeholder"      # openai_dalle, stable_diffusion, placeholder
  image_model: "dall-e-3"            # dall-e-3, sd_xl_base_1.0
  temperature: 0.7                   # Креативность (0.0-1.0)

# Брендинг
branding:
  style: "ssvproff_v1"
  logo_path: "./assets/ssvproff_logo.png"

# Форматирование
formatting:
  output_format: "pdf"               # pdf, epub, html
  template: "academic"               # academic, medical, fiction, professional

# Open Science
open_science:
  generate_artifacts: true           # Сохранять артефакты генерации
  generate_readme: true              # Создавать README в пакете
```

---

## 📖 Примеры использования

### Пример 1: Научная книга

**Конфигурация:** `templates/examples/scientific_book_config.yaml`

```bash
python main.py \
  --input_file input/research_notes.txt \
  --config templates/examples/scientific_book_config.yaml
```

**Результат:** PDF книга в академическом стиле

### Пример 2: Медицинское руководство

**Конфигурация:** `templates/examples/medical_book_config.yaml`

```bash
python main.py \
  --input_file input/clinical_guidelines.txt \
  --config templates/examples/medical_book_config.yaml
```

**Результат:** Профессиональное медицинское руководство

### Пример 3: Художественная книга (EPUB)

**Конфигурация:** `templates/examples/fiction_book_config.yaml`

```bash
python main.py \
  --input_file input/story_ideas.txt \
  --config templates/examples/fiction_book_config.yaml
```

**Результат:** EPUB книга для электронных ридеров

### Пример 4: Подробный режим (отладка)

```bash
python main.py \
  --input_file input/my_ideas.txt \
  --verbose
```

---

## 🏗️ Архитектура

### Структура проекта

```
ssv-book-generator/
├── main.py                          # Точка входа, оркестрация
├── modules/                         # Основные модули
│   ├── ai_content_generator.py     # Генерация контента через ИИ API
│   ├── image_generator.py          # Генерация обложек и иллюстраций
│   ├── book_formatter.py           # Форматирование в PDF/EPUB/HTML
│   └── book_packager.py            # Упаковка финального продукта
├── tests/                           # Модульные и интеграционные тесты
├── templates/                       # Шаблоны стилей и примеры
│   ├── styles/                     # CSS и стили оформления
│   └── examples/                   # Примеры конфигураций
├── input/                           # Входные данные
├── output/                          # Результаты генерации
└── utils/                           # Вспомогательные утилиты
```

### Процесс генерации (Pipeline)

```
[Входной файл] 
    ↓
[1. AI Content Generator]
    → Генерация заголовка
    → Генерация описания
    → Генерация оглавления
    → Генерация глав
    ↓
[2. Image Generator]
    → Генерация обложки
    → Генерация иллюстраций
    ↓
[3. Book Formatter]
    → Форматирование в PDF/EPUB
    → Применение стилей
    → Вставка изображений
    ↓
[4. Book Packager]
    → Упаковка файлов
    → Создание артефактов
    → Генерация README
    ↓
[Финальный пакет]
```

### Модули

#### 1. `ai_content_generator.py`

**Функции:**
- `load_config(config_path)` - Загрузка конфигурации
- `generate_content_from_transcript(transcript, config_path)` - Основная функция генерации

**Поддерживаемые провайдеры:**
- OpenAI GPT (gpt-4o, gpt-3.5-turbo)
- Anthropic Claude (claude-3-opus, claude-3-sonnet)

#### 2. `image_generator.py`

**Функции:**
- `generate_cover(title, book_type, config_path)` - Генерация обложки
- `generate_illustrations(content_chunks, config_path)` - Генерация иллюстраций

**Поддерживаемые провайдеры:**
- OpenAI DALL-E 3
- Stability AI (Stable Diffusion XL)
- Placeholder (для тестирования)

#### 3. `book_formatter.py`

**Функции:**
- `format_to_format_type(content_dict, cover_path, illustrations_paths, config_path)` - Основная функция форматирования

**Поддерживаемые форматы:**
- PDF (через fpdf2)
- EPUB (через ebooklib)
- HTML (нативная генерация)

#### 4. `book_packager.py`

**Функции:**
- `create_package(formatted_book_path, content_dict, ...)` - Создание финального пакета

**Возможности:**
- Структурированная упаковка
- Генерация метаданных
- Open Science артефакты
- Автоматическое README

---

## 🛠️ Разработка

### Настройка окружения разработки

```bash
# Клонирование
git clone https://github.com/Serg2206/ssv-book-generator.git
cd ssv-book-generator

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей + dev зависимости
pip install -r requirements.txt

# Установка pre-commit hooks (опционально)
pip install pre-commit
pre-commit install
```

### Структура модулей

Каждый модуль следует принципу единой ответственности:

- **ai_content_generator**: Отвечает только за генерацию текста
- **image_generator**: Отвечает только за генерацию изображений
- **book_formatter**: Отвечает только за форматирование
- **book_packager**: Отвечает только за упаковку

### Логирование

Все модули используют стандартный Python `logging`:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.debug("Отладочная информация")
```

Логи сохраняются в файл `book_generator.log`.

### Обработка ошибок

Все модули используют try-except блоки для graceful degradation:

```python
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}")
    # Fallback логика
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

---

## 🧪 Тестирование

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием кода

```bash
pytest --cov=modules --cov-report=html
```

Отчёт о покрытии будет сгенерирован в `htmlcov/index.html`.

### Запуск конкретных тестов

```bash
# Модульные тесты для AI генератора
pytest tests/test_ai_content_generator.py

# Интеграционные тесты
pytest tests/test_integration.py

# С подробным выводом
pytest -v

# С отображением print()
pytest -s
```

### Структура тестов

```
tests/
├── __init__.py
├── conftest.py                      # Общие фикстуры
├── test_ai_content_generator.py     # Тесты для AI модуля
├── test_image_generator.py          # Тесты для генерации изображений
├── test_book_formatter.py           # Тесты для форматирования
├── test_book_packager.py            # Тесты для упаковки
└── test_integration.py              # Интеграционные тесты
```

### Моки для тестирования

Тесты используют моки для API вызовов:

```python
@patch('modules.ai_content_generator._call_ai_model')
def test_generate_content(mock_ai_call):
    mock_ai_call.return_value = "Mocked response"
    # Ваш тест здесь
```

---

## 🤝 Вклад в развитие

Мы приветствуем вклад в развитие проекта! 

### Процесс внесения изменений

1. **Fork** репозитория
2. Создайте **feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** ваши изменения (`git commit -m 'Add some AmazingFeature'`)
4. **Push** в branch (`git push origin feature/AmazingFeature`)
5. Откройте **Pull Request**

### Стандарты кода

- Следуйте [PEP 8](https://pep8.org/) для Python кода
- Используйте type hints где возможно
- Добавляйте docstrings для всех публичных функций и классов
- Пишите тесты для новой функциональности
- Обновляйте документацию при необходимости

### Примеры docstrings

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Краткое описание функции.
    
    Подробное описание того, что делает функция.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
        
    Returns:
        Описание возвращаемого значения
        
    Raises:
        ValueError: Когда происходит эта ошибка
        
    Examples:
        >>> my_function("test", 42)
        True
    """
    pass
```

### Отчёт об ошибках

При обнаружении ошибки, пожалуйста:

1. Проверьте [существующие issues](https://github.com/Serg2206/ssv-book-generator/issues)
2. Создайте новый issue с:
   - Описанием проблемы
   - Шагами для воспроизведения
   - Ожидаемым поведением
   - Фактическим поведением
   - Версией Python и ОС
   - Логами (если применимо)

---

## 📚 Дополнительные ресурсы

### Документация API

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Stability AI Documentation](https://platform.stability.ai/docs/getting-started)

### Библиотеки

- [fpdf2](https://pyfpdf.github.io/fpdf2/) - PDF генерация
- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB генерация
- [Pillow](https://pillow.readthedocs.io/) - Обработка изображений

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.

---

## 👨‍🔬 Автор

**Профессор С.В. Сушков**

Разработано для медицинского и научного сообщества с целью ускорения создания качественных образовательных и профессиональных материалов.

---

## 🌟 Благодарности

- Медицинскому сообществу за вдохновение
- Open Source сообществу за отличные инструменты
- OpenAI и Anthropic за мощные ИИ модели

---

## 📞 Контакты

- **GitHub**: [Serg2206/ssv-book-generator](https://github.com/Serg2206/ssv-book-generator)
- **Issues**: [GitHub Issues](https://github.com/Serg2206/ssv-book-generator/issues)

---

**Создано с ❤️ с помощью SSVproff Book Generator**


---

## 🆕 Version 2.1 - Architecture Improvements

### 📦 New Infrastructure Modules

Версия 2.1 добавляет мощную инфраструктуру для надежной работы генератора:

#### `utils/error_handler.py`
- **Кастомные исключения**: `SSVBookGeneratorError`, `ValidationError`, `APIError`, `FileProcessingError`
- **Декоратор `@retry_on_error`**: Автоматические повторные попытки при сбоях
- **Декоратор `@handle_api_errors`**: Обработка ошибок API
- **Context manager `safe_execute`**: Безопасное выполнение операций

```python
from utils.error_handler import retry_on_error, APIError

@retry_on_error(max_attempts=3, delay=1.0)
def generate_content(prompt):
    # Автоматически повторит до 3 раз при ошибке
    return ai_client.generate(prompt)
```

#### `utils/logger.py`
- **Цветное консольное логирование**: Разные цвета для разных уровней
- **JSON логи**: Структурированные логи для анализа
- **Декоратор `@log_function_call`**: Автоматическое логирование функций
- **Измерение времени выполнения**: Автоматический профайлинг

```python
from utils.logger import setup_logger, log_function_call

logger = setup_logger(__name__, log_file="app.log")

@log_function_call()
def process_chapters(chapters):
    # Автоматически логирует вызов, аргументы и время выполнения
    return [process(ch) for ch in chapters]
```

#### `utils/validator.py`
- **Pydantic модели**: `BookMetadata`, `ChapterData`, `BookConfig`
- **Енумы**: `OutputFormat`, `LogLevel`
- **Валидационные функции**: `validate_file_path()`, `validate_chapters()`
- **Строгая типизация**: Автоматическая валидация данных

```python
from utils.validator import BookMetadata, ChapterData, validate_chapters

metadata = BookMetadata(
    title="Medical Guide",
    author="Dr. Smith",
    language="en"
)

chapters = [
    ChapterData(chapter_num=1, title="Intro", content="...")
]
validate_chapters(chapters)  # Проверит корректность
```

### 🚀 Enhanced Generator Modules

#### `modules/book_generator_v2.py`
**6-этапный пайплайн генерации**:
1. 📖 Чтение input файла
2. 📝 Генерация метаданных
3. 📚 Генерация глав
4. 🖼️ Генерация изображений
5. 📄 Форматирование
6. 📦 Упаковка результата

**Полная интеграция с utils**:
- Автоматический retry при ошибках API
- Детальное логирование каждого этапа
- Валидация всех данных
- Progress bars для визуализации прогресса

```python
from modules.book_generator_v2 import BookGeneratorV2

generator = BookGeneratorV2(api_key="your-key")
book = generator.generate(
    input_file="surgical_topics.txt",
    output_dir="output"
)
```

#### `modules/chapter_generator.py`
**Параллельная обработка**:
- `ThreadPoolExecutor` для одновременной генерации глав
- Настраиваемое количество воркеров
- Fallback на последовательную обработку

**Интеллектуальное кеширование**:
- MD5-based кеш ключи
- Автоматическое переиспользование контента
- Методы управления кешем (clear, stats)

```python
from modules.chapter_generator import ChapterGenerator

generator = ChapterGenerator(api_key="key")
chapters = generator.generate_chapters_parallel(
    sections=topics,
    max_workers=4,  # 4 параллельных запроса
    use_cache=True  # Использовать кеш
)
```

#### `modules/book_formatter.py` (обновлен)
**Улучшенное форматирование**:
- Интеграция с `BookMetadata` и `ChapterData`
- Error handling с `@handle_api_errors`
- Валидация входных данных
- Поддержка PDF, EPUB, HTML

### 🧪 Comprehensive Testing

Добавлены pytest тесты:
- `tests/test_error_handler.py` (197 строк)
- `tests/test_logger.py` (249 строк)
- `tests/test_validator.py` (293 строк)

**Покрытие**:
- Unit тесты для всех модулей
- Integration тесты
- Edge cases и error scenarios

```bash
# Запуск тестов
pytest tests/ -v

# С покрытием
pytest tests/ --cov=utils --cov=modules
```

### 📋 Updated Dependencies

```
pydantic>=2.0.0      # Валидация данных
colorama>=0.4.6      # Цветной вывод
pytest>=7.4.0        # Тестирование
pytest-cov>=4.1.0    # Coverage reports
```

### 🎯 Migration Guide v1.0 → v2.1

**Старый код (v1.0)**:
```python
from modules.book_generator import BookGenerator

generator = BookGenerator()
book = generator.generate(input_file)
```

**Новый код (v2.1)**:
```python
from modules.book_generator_v2 import BookGeneratorV2
from utils.logger import setup_logger

logger = setup_logger(__name__)

generator = BookGeneratorV2(api_key="key")
book = generator.generate(
    input_file="topics.txt",
    output_dir="output",
    parallel=True,
    use_cache=True
)
```

**Преимущества v2.1**:
- ✅ Автоматический retry при ошибках
- ✅ Детальное логирование
- ✅ Валидация данных
- ✅ Параллельная обработка
- ✅ Кеширование результатов
- ✅ Полное тестовое покрытие

---

