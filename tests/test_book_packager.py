
"""
Модульные тесты для book_packager
"""
import pytest
from pathlib import Path
from modules import book_packager


class TestCreatePackage:
    """Тесты для функции create_package"""
    
    def test_create_package_basic(self, config_file, sample_content_dict, temp_output_dir):
        """Тест создания базового пакета"""
        # Создаем временный файл книги
        book_file = temp_output_dir / "test_book.pdf"
        book_file.write_text("Mock PDF content")
        
        package_path = book_packager.create_package(
            formatted_book_path=str(book_file),
            content_dict=sample_content_dict,
            illustrations_paths=[],
            config_path=config_file
        )
        
        assert package_path is not None
        assert Path(package_path).exists()
        assert Path(package_path).is_dir()
        
        # Проверяем наличие ключевых файлов
        assert (Path(package_path) / "README.md").exists()
        assert (Path(package_path) / "metadata.json").exists()
    
    def test_create_package_with_artifacts(self, config_file, sample_content_dict, temp_output_dir):
        """Тест создания пакета с артефактами"""
        book_file = temp_output_dir / "test_book.pdf"
        book_file.write_text("Mock PDF")
        
        # Создаем временные иллюстрации
        img1 = temp_output_dir / "img1.png"
        img2 = temp_output_dir / "img2.png"
        img1.touch()
        img2.touch()
        
        package_path = book_packager.create_package(
            formatted_book_path=str(book_file),
            content_dict=sample_content_dict,
            illustrations_paths=[str(img1), str(img2)],
            config_path=config_file
        )
        
        # Проверяем артефакты
        artifacts_dir = Path(package_path) / "artifacts"
        assert artifacts_dir.exists()
        assert (artifacts_dir / "content.json").exists()
        assert (artifacts_dir / "images").exists()
    
    def test_create_package_nonexistent_book(self, config_file, sample_content_dict):
        """Тест с несуществующим файлом книги"""
        with pytest.raises(FileNotFoundError):
            book_packager.create_package(
                formatted_book_path="nonexistent.pdf",
                content_dict=sample_content_dict,
                illustrations_paths=[],
                config_path=config_file
            )
