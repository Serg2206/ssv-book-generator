
"""
Модульные тесты для image_generator
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from modules import image_generator


class TestGenerateCover:
    """Тесты для функции generate_cover"""
    
    def test_generate_cover_placeholder(self, config_file, temp_output_dir):
        """Тест генерации обложки с заглушкой"""
        cover_path = image_generator.generate_cover(
            title="Test Book",
            book_type="scientific",
            config_path=config_file
        )
        
        assert cover_path is not None
        assert Path(cover_path).exists()
    
    def test_generate_cover_invalid_config(self):
        """Тест с невалидной конфигурацией"""
        with pytest.raises(FileNotFoundError):
            image_generator.generate_cover(
                title="Test",
                book_type="scientific",
                config_path="nonexistent.yaml"
            )


class TestGenerateIllustrations:
    """Тесты для функции generate_illustrations"""
    
    def test_generate_illustrations_placeholder(self, config_file, sample_content_dict):
        """Тест генерации иллюстраций с заглушками"""
        illustrations = image_generator.generate_illustrations(
            content_chunks=sample_content_dict['chapters'],
            config_path=config_file,
            max_illustrations=2
        )
        
        assert isinstance(illustrations, list)
        assert len(illustrations) == 2
        assert all(Path(path).exists() for path in illustrations)
    
    def test_generate_illustrations_empty_chunks(self, config_file):
        """Тест с пустым списком глав"""
        illustrations = image_generator.generate_illustrations(
            content_chunks=[],
            config_path=config_file
        )
        
        assert illustrations == []
