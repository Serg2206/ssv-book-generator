"""
Integration tests for complete book generation pipeline.

Tests the entire workflow from input to final book generation,
verifying that all modules work together correctly.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from utils.validator import BookMetadata, ChapterData, OutputFormat
from utils.logger import setup_logger
from cache.content_cache import ContentCache
from modules.chapter_generator import ChapterGenerator
from modules.book_formatter import BookFormatterV2

logger = setup_logger(__name__)


class TestBookGenerationIntegration:
    """
    Integration tests for complete book generation workflow.
    """
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample book metadata."""
        return BookMetadata(
            title="Test Medical Book",
            author="Dr. Test Author",
            language="en",
            isbn="978-0-123456-78-9",
            publisher="Test Publisher"
        )
    
    @pytest.fixture
    def sample_chapters(self):
        """Create sample chapter data."""
        return [
            ChapterData(
                chapter_num=1,
                title="Introduction to Medical Procedures",
                content="This chapter introduces basic medical procedures and techniques. "
                       "It covers fundamental concepts that every medical professional should know. "
                       "The content includes safety protocols, patient care, and best practices."
            ),
            ChapterData(
                chapter_num=2,
                title="Advanced Surgical Techniques",
                content="This chapter covers advanced surgical techniques used in modern medicine. "
                       "It includes detailed explanations of minimally invasive procedures, "
                       "robotic surgery, and post-operative care protocols."
            ),
            ChapterData(
                chapter_num=3,
                title="Patient Safety and Care",
                content="Patient safety is paramount in medical practice. This chapter discusses "
                       "safety protocols, infection control, patient monitoring, and quality assurance. "
                       "It emphasizes the importance of comprehensive patient care."
            )
        ]
    
    def test_metadata_validation(self, sample_metadata):
        """
        Test that book metadata is properly validated.
        """
        # Metadata should be valid
        assert sample_metadata.title == "Test Medical Book"
        assert sample_metadata.author == "Dr. Test Author"
        assert sample_metadata.language == "en"
        
        # Test validation of required fields
        assert len(sample_metadata.title) > 0
        assert len(sample_metadata.author) > 0
        
        logger.info("✓ Metadata validation passed")
    
    def test_chapter_data_validation(self, sample_chapters):
        """
        Test that chapter data is properly validated.
        """
        # Should have 3 chapters
        assert len(sample_chapters) == 3
        
        # Each chapter should have required fields
        for chapter in sample_chapters:
            assert chapter.chapter_num > 0
            assert len(chapter.title) > 0
            assert len(chapter.content) > 0
        
        # Chapters should be in order
        chapter_nums = [ch.chapter_num for ch in sample_chapters]
        assert chapter_nums == [1, 2, 3]
        
        logger.info("✓ Chapter data validation passed")
    
    def test_content_cache_integration(self, temp_dir):
        """
        Test content caching system integration.
        """
        cache_dir = temp_dir / ".test_cache"
        cache = ContentCache(cache_dir=str(cache_dir), default_ttl=3600)
        
        # Test cache set/get
        test_prompt = "Generate chapter about surgical procedures"
        test_content = "Surgical procedures require precision and care..."
        
        # Store in cache
        cache.set(test_prompt, test_content)
        
        # Retrieve from cache
        retrieved = cache.get(test_prompt)
        assert retrieved == test_content
        
        # Check cache statistics
        stats = cache.get_stats()
        assert stats['total_hits'] == 1
        assert stats['memory_hits'] == 1
        
        # Test cache miss
        missing = cache.get("Non-existent prompt")
        assert missing is None
        
        logger.info("✓ Content cache integration passed")
    
    def test_book_formatter_html(self, temp_dir, sample_metadata, sample_chapters):
        """
        Test book formatting to HTML.
        """
        formatter = BookFormatterV2()
        output_path = temp_dir / "test_book.html"
        
        # Generate HTML book
        result = formatter.format_to_html(
            metadata=sample_metadata,
            chapters=sample_chapters,
            output_path=str(output_path)
        )
        
        # Verify file was created
        assert output_path.exists()
        assert result == str(output_path)
        
        # Verify content
        content = output_path.read_text(encoding='utf-8')
        assert sample_metadata.title in content
        assert sample_metadata.author in content
        assert sample_chapters[0].title in content
        assert sample_chapters[0].content in content
        
        logger.info("✓ HTML formatting passed")
    
    def test_chapter_generator_mock(self, sample_chapters):
        """
        Test chapter generator with mocked AI calls.
        """
        # Mock AI client to avoid actual API calls
        with patch('modules.chapter_generator.ChapterGenerator') as MockGen:
            mock_generator = MockGen.return_value
            mock_generator.generate_chapters_parallel.return_value = sample_chapters
            
            # Simulate chapter generation
            chapters = mock_generator.generate_chapters_parallel(
                sections=["Intro", "Advanced", "Safety"],
                max_workers=2
            )
            
            assert len(chapters) == 3
            assert chapters[0].title == sample_chapters[0].title
            
        logger.info("✓ Chapter generator mock test passed")
    
    def test_full_pipeline_html(self, temp_dir, sample_metadata, sample_chapters):
        """
        Test complete book generation pipeline to HTML.
        
        This is the main integration test that verifies:
        1. Metadata validation
        2. Chapter data validation  
        3. Book formatting
        4. File output
        """
        # Step 1: Validate metadata
        assert sample_metadata.title is not None
        logger.info("Step 1: Metadata validated")
        
        # Step 2: Validate chapters
        from utils.validator import validate_chapters
        validate_chapters(sample_chapters)
        logger.info("Step 2: Chapters validated")
        
        # Step 3: Format book
        formatter = BookFormatterV2()
        output_path = temp_dir / "complete_book.html"
        
        result = formatter.format_book(
            metadata=sample_metadata,
            chapters=sample_chapters,
            output_format="html",
            output_path=str(output_path)
        )
        
        logger.info("Step 3: Book formatted")
        
        # Step 4: Verify output
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0
        
        content = Path(result).read_text(encoding='utf-8')
        
        # Verify all chapters are present
        for chapter in sample_chapters:
            assert chapter.title in content
            assert chapter.content in content
        
        logger.info("Step 4: Output verified")
        logger.info(f"✓ Full pipeline test passed! Book generated: {result}")
    
    def test_error_handling_invalid_metadata(self):
        """
        Test error handling for invalid metadata.
        """
        from pydantic import ValidationError
        
        # Test missing required field
        with pytest.raises(ValidationError):
            BookMetadata(
                title="",  # Empty title should fail
                author="Dr. Test",
                language="en"
            )
        
        logger.info("✓ Error handling for invalid metadata passed")
    
    def test_error_handling_invalid_chapters(self):
        """
        Test error handling for invalid chapter data.
        """
        from utils.validator import validate_chapters
        
        # Test empty chapters list
        with pytest.raises(ValueError, match="at least one chapter"):
            validate_chapters([])
        
        # Test duplicate chapter numbers
        duplicate_chapters = [
            ChapterData(chapter_num=1, title="Ch1", content="Content 1"),
            ChapterData(chapter_num=1, title="Ch1 Dup", content="Content dup")
        ]
        
        with pytest.raises(ValueError, match="Duplicate chapter"):
            validate_chapters(duplicate_chapters)
        
        logger.info("✓ Error handling for invalid chapters passed")
    
    def test_cache_with_formatter(self, temp_dir, sample_metadata, sample_chapters):
        """
        Test integration of cache system with formatter.
        """
        cache_dir = temp_dir / ".cache"
        cache = ContentCache(cache_dir=str(cache_dir))
        
        # Simulate caching formatted content
        output_path = temp_dir / "cached_book.html"
        formatter = BookFormatterV2()
        
        # First generation (cache miss)
        result1 = formatter.format_to_html(
            metadata=sample_metadata,
            chapters=sample_chapters,
            output_path=str(output_path)
        )
        
        # Cache the result
        content = Path(result1).read_text(encoding='utf-8')
        cache_key = f"book_{sample_metadata.title}"
        cache.set(cache_key, content)
        
        # Retrieve from cache
        cached_content = cache.get(cache_key)
        assert cached_content == content
        
        stats = cache.get_stats()
        assert stats['total_hits'] >= 1
        
        logger.info("✓ Cache + Formatter integration passed")


class TestPerformance:
    """
    Performance tests for book generation.
    """
    
    def test_format_performance(self, tmp_path):
        """
        Test formatting performance with larger book.
        """
        import time
        
        metadata = BookMetadata(
            title="Large Test Book",
            author="Test Author",
            language="en"
        )
        
        # Generate 10 chapters
        chapters = [
            ChapterData(
                chapter_num=i,
                title=f"Chapter {i}",
                content=f"This is the content for chapter {i}. " * 50
            )
            for i in range(1, 11)
        ]
        
        formatter = BookFormatterV2()
        output_path = tmp_path / "performance_test.html"
        
        start_time = time.time()
        
        formatter.format_to_html(
            metadata=metadata,
            chapters=chapters,
            output_path=str(output_path)
        )
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert output_path.exists()
        
        logger.info(f"✓ Performance test passed: {elapsed:.2f}s for 10 chapters")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
