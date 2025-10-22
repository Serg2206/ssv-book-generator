
"""
Модульные тесты для book_formatter
"""
import pytest
from pathlib import Path
from modules import book_formatter


class TestFormatToPDF:
    """Тесты для форматирования в PDF"""
    
    def test_format_pdf_basic(self, config_file, sample_content_dict, temp_output_dir):
        """Тест базового форматирования PDF"""
        # Создаем временную обложку
        cover_path = temp_output_dir / "cover.png"
        cover_path.touch()
        
        pdf_path = book_formatter.format_to_format_type(
            content_dict=sample_content_dict,
            cover_path=str(cover_path),
            illustrations_paths=[],
            config_path=config_file
        )
        
        assert pdf_path is not None
        assert Path(pdf_path).exists()
        assert pdf_path.endswith('.pdf')


class TestFormatToEPUB:
    """Тесты для форматирования в EPUB"""
    
    def test_format_epub_basic(self, config_file, sample_content_dict, temp_output_dir, tmp_path):
        """Тест базового форматирования EPUB"""
        # Обновляем конфигурацию для EPUB
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        config['formatting']['output_format'] = 'epub'
        
        epub_config = tmp_path / "epub_config.yaml"
        with open(epub_config, 'w') as f:
            yaml.dump(config, f)
        
        cover_path = temp_output_dir / "cover.png"
        cover_path.touch()
        
        epub_path = book_formatter.format_to_format_type(
            content_dict=sample_content_dict,
            cover_path=str(cover_path),
            illustrations_paths=[],
            config_path=str(epub_config)
        )
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        assert epub_path.endswith('.epub')
