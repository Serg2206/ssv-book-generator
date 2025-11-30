"""
Unit tests for validator module.

Tests Pydantic models, enums, and validation utility functions.
"""

import pytest
from pathlib import Path
from typing import List
from pydantic import ValidationError as PydanticValidationError

from utils.validator import (
    BookMetadata,
    ChapterData,
    BookConfig,
    OutputFormat,
    LogLevel,
    validate_file_path,
    validate_chapters
)


class TestOutputFormatEnum:
    """Test OutputFormat enum."""
    
    def test_output_format_values(self):
        """Test OutputFormat enum has correct values."""
        assert OutputFormat.PDF == "pdf"
        assert OutputFormat.EPUB == "epub"
        assert OutputFormat.HTML == "html"
    
    def test_output_format_iteration(self):
        """Test can iterate over OutputFormat values."""
        formats = [f.value for f in OutputFormat]
        assert "pdf" in formats
        assert "epub" in formats
        assert "html" in formats


class TestLogLevelEnum:
    """Test LogLevel enum."""
    
    def test_log_level_values(self):
        """Test LogLevel enum has correct values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"


class TestBookMetadata:
    """Test BookMetadata Pydantic model."""
    
    def test_book_metadata_valid(self):
        """Test creating valid BookMetadata."""
        metadata = BookMetadata(
            title="Test Book",
            author="John Doe",
            language="en"
        )
        assert metadata.title == "Test Book"
        assert metadata.author == "John Doe"
        assert metadata.language == "en"
    
    def test_book_metadata_optional_fields(self):
        """Test BookMetadata with optional fields."""
        metadata = BookMetadata(
            title="Test Book",
            author="Jane Doe",
            language="en",
            isbn="978-3-16-148410-0",
            publisher="Test Publisher"
        )
        assert metadata.isbn == "978-3-16-148410-0"
        assert metadata.publisher == "Test Publisher"
    
    def test_book_metadata_missing_required(self):
        """Test BookMetadata raises error for missing required fields."""
        with pytest.raises(PydanticValidationError):
            BookMetadata(title="Test Book")
    
    def test_book_metadata_empty_title(self):
        """Test BookMetadata validates non-empty title."""
        with pytest.raises(PydanticValidationError):
            BookMetadata(title="", author="John Doe", language="en")


class TestChapterData:
    """Test ChapterData Pydantic model."""
    
    def test_chapter_data_valid(self):
        """Test creating valid ChapterData."""
        chapter = ChapterData(
            chapter_num=1,
            title="Chapter 1",
            content="This is chapter 1 content."
        )
        assert chapter.chapter_num == 1
        assert chapter.title == "Chapter 1"
        assert chapter.content == "This is chapter 1 content."
    
    def test_chapter_data_with_images(self):
        """Test ChapterData with image URLs."""
        chapter = ChapterData(
            chapter_num=1,
            title="Chapter 1",
            content="Content",
            images=["http://example.com/img1.jpg", "http://example.com/img2.jpg"]
        )
        assert len(chapter.images) == 2
        assert chapter.images[0] == "http://example.com/img1.jpg"
    
    def test_chapter_data_positive_number(self):
        """Test ChapterData validates positive chapter_num."""
        with pytest.raises(PydanticValidationError):
            ChapterData(
                chapter_num=0,
                title="Chapter 0",
                content="Content"
            )
    
    def test_chapter_data_invalid_image_url(self):
        """Test ChapterData validates image URLs."""
        with pytest.raises(PydanticValidationError):
            ChapterData(
                chapter_num=1,
                title="Chapter 1",
                content="Content",
                images=["not-a-valid-url"]
            )


class TestBookConfig:
    """Test BookConfig Pydantic model."""
    
    def test_book_config_default(self):
        """Test BookConfig with default values."""
        config = BookConfig(
            title="Test Book",
            author="Test Author"
        )
        assert config.title == "Test Book"
        assert config.author == "Test Author"
        assert config.output_format == OutputFormat.PDF  # default
    
    def test_book_config_with_format(self):
        """Test BookConfig with specific output format."""
        config = BookConfig(
            title="Test Book",
            author="Test Author",
            output_format=OutputFormat.EPUB
        )
        assert config.output_format == OutputFormat.EPUB
    
    def test_book_config_with_log_level(self):
        """Test BookConfig with log level."""
        config = BookConfig(
            title="Test Book",
            author="Test Author",
            log_level=LogLevel.DEBUG
        )
        assert config.log_level == LogLevel.DEBUG
    
    def test_book_config_with_api_config(self):
        """Test BookConfig with API configuration."""
        config = BookConfig(
            title="Test Book",
            author="Test Author",
            api_key="test-key",
            max_retries=5
        )
        assert config.api_key == "test-key"
        assert config.max_retries == 5


class TestValidateFilePath:
    """Test validate_file_path function."""
    
    def test_validate_existing_file(self, tmp_path):
        """Test validating existing file path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Should not raise
        validate_file_path(str(test_file), must_exist=True)
    
    def test_validate_non_existing_file_required(self, tmp_path):
        """Test validating non-existing file when required."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(ValueError, match="does not exist"):
            validate_file_path(str(test_file), must_exist=True)
    
    def test_validate_new_file_path(self, tmp_path):
        """Test validating path for new file."""
        test_file = tmp_path / "new_file.txt"
        
        # Should not raise
        validate_file_path(str(test_file), must_exist=False)
    
    def test_validate_directory_not_file(self, tmp_path):
        """Test validating directory path when file expected."""
        # Should raise error if directory is passed
        with pytest.raises(ValueError, match="is a directory"):
            validate_file_path(str(tmp_path), must_exist=True)


class TestValidateChapters:
    """Test validate_chapters function."""
    
    def test_validate_valid_chapters(self):
        """Test validating correct chapter list."""
        chapters = [
            ChapterData(chapter_num=1, title="Ch1", content="Content 1"),
            ChapterData(chapter_num=2, title="Ch2", content="Content 2"),
            ChapterData(chapter_num=3, title="Ch3", content="Content 3")
        ]
        
        # Should not raise
        validate_chapters(chapters)
    
    def test_validate_empty_chapters(self):
        """Test validating empty chapter list."""
        with pytest.raises(ValueError, match="at least one chapter"):
            validate_chapters([])
    
    def test_validate_duplicate_chapter_numbers(self):
        """Test validating chapters with duplicate numbers."""
        chapters = [
            ChapterData(chapter_num=1, title="Ch1", content="Content 1"),
            ChapterData(chapter_num=1, title="Ch1 Dup", content="Content 1 dup"),
            ChapterData(chapter_num=2, title="Ch2", content="Content 2")
        ]
        
        with pytest.raises(ValueError, match="Duplicate chapter"):
            validate_chapters(chapters)
    
    def test_validate_non_sequential_chapters(self):
        """Test validating non-sequential chapter numbers."""
        chapters = [
            ChapterData(chapter_num=1, title="Ch1", content="Content 1"),
            ChapterData(chapter_num=3, title="Ch3", content="Content 3"),
            ChapterData(chapter_num=5, title="Ch5", content="Content 5")
        ]
        
        # Non-sequential should still be valid, just check for duplicates
        validate_chapters(chapters)


class TestIntegration:
    """Integration tests for validation."""
    
    def test_complete_book_validation(self):
        """Test validating complete book structure."""
        metadata = BookMetadata(
            title="Complete Book",
            author="Test Author",
            language="en"
        )
        
        chapters = [
            ChapterData(chapter_num=i, title=f"Chapter {i}", content=f"Content {i}")
            for i in range(1, 6)
        ]
        
        config = BookConfig(
            title=metadata.title,
            author=metadata.author,
            output_format=OutputFormat.PDF
        )
        
        # Validate all components
        assert metadata.title == config.title
        assert len(chapters) == 5
        validate_chapters(chapters)
    
    def test_model_to_dict(self):
        """Test converting Pydantic models to dict."""
        metadata = BookMetadata(
            title="Test",
            author="Author",
            language="en"
        )
        
        metadata_dict = metadata.model_dump()
        assert metadata_dict["title"] == "Test"
        assert metadata_dict["author"] == "Author"
        assert "language" in metadata_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
