
"""
Интеграционные тесты для полного цикла генерации книги
"""
import pytest
from unittest.mock import patch
from pathlib import Path
import main


class TestFullPipeline:
    """Тесты полного цикла генерации"""
    
    @patch('modules.ai_content_generator._call_ai_model')
    def test_full_generation_pipeline(self, mock_ai_call, config_file, sample_transcript, tmp_path):
        """Тест полного цикла генерации книги"""
        # Создаем входной файл
        input_file = tmp_path / "input.txt"
        input_file.write_text(sample_transcript)
        
        # Моки для ИИ вызовов
        mock_ai_call.side_effect = [
            'Integration Test Book',
            'This is a test book description for integration testing.',
            'Глава 1: First\nГлава 2: Second',
            'Content of first chapter...' * 50,
            'Content of second chapter...' * 50,
        ]
        
        # Запускаем генерацию
        package_path = main.generate_book(
            input_file=str(input_file),
            config_file=config_file
        )
        
        assert package_path is not None
        assert Path(package_path).exists()
        
        # Проверяем структуру пакета
        package_dir = Path(package_path)
        assert (package_dir / "README.md").exists()
        assert (package_dir / "metadata.json").exists()
        assert (package_dir / "artifacts").exists()
        
        # Проверяем наличие книги (PDF или EPUB)
        book_files = list(package_dir.glob("*.pdf")) + list(package_dir.glob("*.epub"))
        assert len(book_files) > 0


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    def test_invalid_input_file(self, config_file):
        """Тест с невалидным входным файлом"""
        result = main.generate_book(
            input_file="nonexistent.txt",
            config_file=config_file
        )
        assert result is None
    
    def test_invalid_config_file(self, tmp_path, sample_transcript):
        """Тест с невалидной конфигурацией"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(sample_transcript)
        
        result = main.generate_book(
            input_file=str(input_file),
            config_file="nonexistent.yaml"
        )
        assert result is None
