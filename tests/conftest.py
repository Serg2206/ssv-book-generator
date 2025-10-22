
"""
Pytest конфигурация и фикстуры для тестов
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path


@pytest.fixture
def sample_config():
    """Базовая тестовая конфигурация"""
    return {
        'project': {
            'name': 'SSVproff Book Generator Test',
            'version': '1.0.0'
        },
        'paths': {
            'input_folder': './test_input',
            'output_folder': './test_output'
        },
        'book': {
            'title': 'Test Book',
            'type': 'scientific',
            'target_audience': 'students',
            'language': 'ru',
            'genre': 'educational'
        },
        'ai': {
            'content_provider': 'openai_gpt',
            'content_model': 'gpt-4o',
            'image_provider': 'placeholder',
            'image_model': 'test',
            'temperature': 0.7
        },
        'branding': {
            'style': 'ssvproff_v1',
            'logo_path': './assets/logo.png'
        },
        'formatting': {
            'output_format': 'pdf',
            'template': 'academic'
        },
        'open_science': {
            'generate_artifacts': True,
            'generate_readme': True
        }
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Создает временный файл конфигурации"""
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f)
    return str(config_path)


@pytest.fixture
def sample_transcript():
    """Пример транскрипции для тестов"""
    return """
    Искусственный интеллект в современной медицине.
    
    В последние годы искусственный интеллект стал неотъемлемой частью медицинской практики.
    Машинное обучение позволяет анализировать медицинские изображения с высокой точностью.
    Нейронные сети способны выявлять паттерны в данных, которые не видны человеческому глазу.
    
    Диагностика заболеваний с помощью ИИ становится всё более точной.
    Алгоритмы глубокого обучения анализируют рентгеновские снимки, МРТ и КТ изображения.
    Это позволяет врачам быстрее ставить диагнозы и принимать решения о лечении.
    
    Персонализированная медицина - еще одна область применения ИИ.
    Анализируя генетические данные пациента, системы ИИ могут предсказывать риски заболеваний.
    Это позволяет разработать индивидуальные планы лечения и профилактики.
    """


@pytest.fixture
def sample_content_dict():
    """Пример результата генерации контента"""
    return {
        'title': 'Искусственный интеллект в медицине',
        'description': 'Книга о применении ИИ в медицинской практике',
        'outline': [
            'Введение в медицинский ИИ',
            'Диагностика с помощью ИИ',
            'Персонализированная медицина'
        ],
        'chapters': [
            {
                'title': 'Введение в медицинский ИИ',
                'content': 'Искусственный интеллект революционизирует медицину...'
            },
            {
                'title': 'Диагностика с помощью ИИ',
                'content': 'Современные алгоритмы позволяют...'
            },
            {
                'title': 'Персонализированная медицина',
                'content': 'Индивидуальный подход к каждому пациенту...'
            }
        ],
        'metadata': {
            'book_type': 'scientific',
            'language': 'ru',
            'target_audience': 'students',
            'themes': ['искусственный', 'интеллект', 'медицина', 'диагностика']
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Создает временную директорию для выходных файлов"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
