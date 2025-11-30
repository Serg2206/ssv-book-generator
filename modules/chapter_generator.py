"""Chapter Generator with parallel processing and caching support.

This module provides:
- Parallel chapter generation using ThreadPoolExecutor
- Result caching to avoid duplicate API calls
- Progress tracking for multiple chapters
- Integration with error handling and logging
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.error_handler import retry_on_error, handle_api_errors, APIError
from utils.logger import setup_logger, log_function_call
from utils.validator import ChapterData

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Setup logger
logger = setup_logger('chapter_generator')

# Simple in-memory cache (in production, use Redis or file-based cache)
CHAPTER_CACHE: Dict[str, ChapterData] = {}


class ChapterGenerator:
    """Generator for book chapters with parallel processing and caching."""
    
    def __init__(self, max_workers: int = 3, use_cache: bool = True):
        """Initialize chapter generator.
        
        Args:
            max_workers: Maximum number of parallel workers
            use_cache: Enable result caching
        """
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.logger = logger
        
        self.logger.info(f"ChapterGenerator initialized (workers={max_workers}, cache={use_cache})")
    
    def _generate_cache_key(self, chapter_num: int, content: str) -> str:
        """Generate cache key for chapter.
        
        Args:
            chapter_num: Chapter number
            content: Chapter content
        
        Returns:
            Cache key (MD5 hash)
        """
        key_data = f"{chapter_num}:{content[:500]}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[ChapterData]:
        """Retrieve chapter from cache.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached chapter data or None
        """
        if not self.use_cache:
            return None
        
        cached = CHAPTER_CACHE.get(cache_key)
        if cached:
            self.logger.debug(f"Cache hit for key: {cache_key[:8]}...")
        return cached
    
    def _save_to_cache(self, cache_key: str, chapter: ChapterData) -> None:
        """Save chapter to cache.
        
        Args:
            cache_key: Cache key
            chapter: Chapter data to cache
        """
        if self.use_cache:
            CHAPTER_CACHE[cache_key] = chapter
            self.logger.debug(f"Cached chapter {chapter.chapter_number}: {cache_key[:8]}...")
    
    @log_function_call(logger)
    @handle_api_errors(provider="AI Content Generator")
    @retry_on_error(max_attempts=3, delay=1.0, exceptions=(APIError,))
    def generate_single_chapter(self, chapter_num: int, content: str, 
                               title: Optional[str] = None) -> ChapterData:
        """Generate a single chapter.
        
        Args:
            chapter_num: Chapter number
            content: Chapter content
            title: Optional chapter title
        
        Returns:
            Generated chapter data
        """
        # Check cache
        cache_key = self._generate_cache_key(chapter_num, content)
        cached_chapter = self._get_from_cache(cache_key)
        
        if cached_chapter:
            self.logger.info(f"Using cached chapter {chapter_num}")
            return cached_chapter
        
        # Generate chapter (in real implementation, this would call AI API)
        self.logger.debug(f"Generating chapter {chapter_num} ({len(content)} chars)")
        
        chapter = ChapterData(
            chapter_number=chapter_num,
            title=title or f"Chapter {chapter_num}",
            content=content,
            summary=content[:200] + "..." if len(content) > 200 else content,
            keywords=self._extract_keywords(content)
        )
        
        # Save to cache
        self._save_to_cache(cache_key, chapter)
        
        self.logger.info(f"Chapter {chapter_num} generated successfully")
        return chapter
    
    def _extract_keywords(self, content: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from content.
        
        Args:
            content: Chapter content
            max_keywords: Maximum number of keywords
        
        Returns:
            List of keywords
        """
        # Simple keyword extraction (in production, use NLP)
        words = content.lower().split()
        # Get most common words (simplified)
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]
    
    @log_function_call(logger)
    def generate_chapters_parallel(self, sections: List[tuple[int, str, Optional[str]]]) -> List[ChapterData]:
        """Generate multiple chapters in parallel.
        
        Args:
            sections: List of (chapter_num, content, title) tuples
        
        Returns:
            List of generated chapters
        """
        self.logger.info(f"Starting parallel generation of {len(sections)} chapters")
        chapters = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_chapter = {
                executor.submit(self.generate_single_chapter, num, content, title): num
                for num, content, title in sections
            }
            
            # Progress bar if available
            if TQDM_AVAILABLE:
                progress = tqdm(total=len(sections), desc="Generating chapters")
            
            # Collect results as they complete
            for future in as_completed(future_to_chapter):
                chapter_num = future_to_chapter[future]
                try:
                    chapter = future.result()
                    chapters.append(chapter)
                    
                    if TQDM_AVAILABLE:
                        progress.update(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate chapter {chapter_num}: {e}")
                    # Create placeholder chapter
                    chapters.append(ChapterData(
                        chapter_number=chapter_num,
                        title=f"Chapter {chapter_num}",
                        content="Error generating chapter content.",
                        summary="Error"
                    ))
            
            if TQDM_AVAILABLE:
                progress.close()
        
        # Sort chapters by number
        chapters.sort(key=lambda c: c.chapter_number)
        
        self.logger.info(f"Parallel generation completed: {len(chapters)} chapters")
        return chapters
    
    @log_function_call(logger)
    def generate_chapters_sequential(self, sections: List[tuple[int, str, Optional[str]]]) -> List[ChapterData]:
        """Generate chapters sequentially (fallback for debugging).
        
        Args:
            sections: List of (chapter_num, content, title) tuples
        
        Returns:
            List of generated chapters
        """
        self.logger.info(f"Starting sequential generation of {len(sections)} chapters")
        chapters = []
        
        # Progress bar if available
        iterator = tqdm(sections, desc="Generating chapters") if TQDM_AVAILABLE else sections
        
        for chapter_num, content, title in iterator:
            try:
                chapter = self.generate_single_chapter(chapter_num, content, title)
                chapters.append(chapter)
            except Exception as e:
                self.logger.error(f"Failed to generate chapter {chapter_num}: {e}")
                # Create placeholder
                chapters.append(ChapterData(
                    chapter_number=chapter_num,
                    title=f"Chapter {chapter_num}",
                    content="Error generating chapter content.",
                    summary="Error"
                ))
        
        self.logger.info(f"Sequential generation completed: {len(chapters)} chapters")
        return chapters
    
    def clear_cache(self) -> None:
        """Clear the chapter cache."""
        global CHAPTER_CACHE
        cache_size = len(CHAPTER_CACHE)
        CHAPTER_CACHE.clear()
        self.logger.info(f"Cleared {cache_size} items from cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "size": len(CHAPTER_CACHE),
            "enabled": self.use_cache,
            "keys": list(CHAPTER_CACHE.keys())
        }


# Convenience functions
@log_function_call(logger)
def generate_chapters(sections: List[tuple[int, str, Optional[str]]],
                     parallel: bool = True,
                     max_workers: int = 3,
                     use_cache: bool = True) -> List[ChapterData]:
    """Generate chapters with automatic parallel/sequential selection.
    
    Args:
        sections: List of (chapter_num, content, title) tuples
        parallel: Use parallel processing
        max_workers: Number of parallel workers
        use_cache: Enable caching
    
    Returns:
        List of generated chapters
    """
    generator = ChapterGenerator(max_workers=max_workers, use_cache=use_cache)
    
    if parallel and len(sections) > 1:
        return generator.generate_chapters_parallel(sections)
    else:
        return generator.generate_chapters_sequential(sections)


if __name__ == "__main__":
    # Example usage
    logger.info("ChapterGenerator module loaded")
    
    # Test with sample data
    test_sections = [
        (1, "Chapter 1 content with medical terminology and procedures.", "Introduction"),
        (2, "Chapter 2 explores advanced surgical techniques.", "Advanced Techniques"),
        (3, "Chapter 3 discusses post-operative care protocols.", "Post-Op Care")
    ]
    
    # Generate chapters
    chapters = generate_chapters(test_sections, parallel=True, max_workers=2)
    logger.info(f"Generated {len(chapters)} chapters successfully")
