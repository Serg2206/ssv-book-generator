"""
AI Content Caching System.

Provides persistent caching for AI-generated content to reduce API calls
and costs. Implements both memory and disk-based caching with TTL support.

Features:
- Multi-level caching (memory + disk)
- TTL (Time To Live) support
- Cache statistics and management
- Thread-safe operations
- Automatic cleanup of expired entries
"""

import os
import json
import hashlib
import time
import pickle
from typing import Any, Optional, Dict, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock

from utils.logger import setup_logger, log_function_call
from utils.error_handler import retry_on_error, safe_execute, FileProcessingError

logger = setup_logger(__name__)


class ContentCache:
    """
    Multi-level caching system for AI-generated content.
    
    Implements both in-memory and disk-based caching with TTL support.
    Thread-safe for concurrent access.
    """
    
    @log_function_call()
    def __init__(self, 
                 cache_dir: str = ".cache",
                 memory_cache_size: int = 100,
                 default_ttl: int = 86400):  # 24 hours
        """
        Initialize content cache.
        
        Args:
            cache_dir: Directory for disk cache
            memory_cache_size: Maximum entries in memory cache
            default_ttl: Default TTL in seconds (24 hours default)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_cache_size = memory_cache_size
        self.default_ttl = default_ttl
        
        # In-memory cache with LRU
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'disk_hits': 0,
            'evictions': 0
        }
        
        logger.info(f"ContentCache initialized: dir={cache_dir}, "
                   f"memory_size={memory_cache_size}, ttl={default_ttl}s")
    
    def _generate_key(self, prompt: str, **kwargs) -> str:
        """
        Generate cache key from prompt and parameters.
        
        Args:
            prompt: AI prompt text
            **kwargs: Additional parameters
            
        Returns:
            MD5 hash as cache key
        """
        # Combine prompt with sorted kwargs
        key_data = f"{prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """
        Check if cache entry is expired.
        
        Args:
            timestamp: Entry creation timestamp
            
        Returns:
            True if expired
        """
        return time.time() - timestamp > self.default_ttl
    
    def _evict_lru(self):
        """
        Evict least recently used item from memory cache.
        """
        if not self._access_times:
            return
        
        # Find LRU item
        lru_key = min(self._access_times, key=self._access_times.get)
        
        # Remove from both caches
        self._memory_cache.pop(lru_key, None)
        self._access_times.pop(lru_key, None)
        
        self._stats['evictions'] += 1
        logger.debug(f"Evicted LRU entry: {lru_key[:8]}...")
    
    @log_function_call()
    @retry_on_error(max_attempts=2)
    def get(self, prompt: str, **kwargs) -> Optional[Any]:
        """
        Get cached content.
        
        Args:
            prompt: AI prompt text
            **kwargs: Additional parameters for key generation
            
        Returns:
            Cached content or None if not found/expired
        """
        key = self._generate_key(prompt, **kwargs)
        
        with self._lock:
            # Check memory cache first
            if key in self._memory_cache:
                content, timestamp = self._memory_cache[key]
                
                if self._is_expired(timestamp):
                    # Remove expired entry
                    self._memory_cache.pop(key)
                    self._access_times.pop(key, None)
                    logger.debug(f"Expired memory cache entry: {key[:8]}...")
                else:
                    # Update access time
                    self._access_times[key] = time.time()
                    self._stats['hits'] += 1
                    self._stats['memory_hits'] += 1
                    logger.info(f"Memory cache hit: {key[:8]}...")
                    return content
            
            # Check disk cache
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                        content, timestamp = data['content'], data['timestamp']
                    
                    if self._is_expired(timestamp):
                        # Remove expired file
                        cache_file.unlink()
                        logger.debug(f"Expired disk cache entry: {key[:8]}...")
                    else:
                        # Load into memory cache
                        self._add_to_memory(key, content, timestamp)
                        
                        self._stats['hits'] += 1
                        self._stats['disk_hits'] += 1
                        logger.info(f"Disk cache hit: {key[:8]}...")
                        return content
                        
                except Exception as e:
                    logger.error(f"Error reading cache file {key[:8]}: {e}")
                    cache_file.unlink(missing_ok=True)
            
            # Cache miss
            self._stats['misses'] += 1
            logger.debug(f"Cache miss: {key[:8]}...")
            return None
    
    def _add_to_memory(self, key: str, content: Any, timestamp: float):
        """
        Add entry to memory cache with LRU eviction.
        
        Args:
            key: Cache key
            content: Content to cache
            timestamp: Entry timestamp
        """
        # Evict if cache is full
        if len(self._memory_cache) >= self.memory_cache_size:
            self._evict_lru()
        
        self._memory_cache[key] = (content, timestamp)
        self._access_times[key] = time.time()
    
    @log_function_call()
    @retry_on_error(max_attempts=2)
    def set(self, prompt: str, content: Any, **kwargs):
        """
        Store content in cache.
        
        Args:
            prompt: AI prompt text
            content: Content to cache
            **kwargs: Additional parameters for key generation
        """
        key = self._generate_key(prompt, **kwargs)
        timestamp = time.time()
        
        with self._lock:
            # Add to memory cache
            self._add_to_memory(key, content, timestamp)
            
            # Save to disk
            try:
                cache_file = self.cache_dir / f"{key}.cache"
                data = {
                    'content': content,
                    'timestamp': timestamp,
                    'prompt': prompt[:100],  # Store first 100 chars for debugging
                    'kwargs': kwargs
                }
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
                
                logger.info(f"Cached content: {key[:8]}...")
                
            except Exception as e:
                logger.error(f"Error writing cache file {key[:8]}: {e}")
    
    @log_function_call()
    def clear(self, memory_only: bool = False):
        """
        Clear cache.
        
        Args:
            memory_only: If True, only clear memory cache
        """
        with self._lock:
            # Clear memory cache
            self._memory_cache.clear()
            self._access_times.clear()
            logger.info("Memory cache cleared")
            
            # Clear disk cache if requested
            if not memory_only:
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.error(f"Error deleting {cache_file}: {e}")
                
                logger.info("Disk cache cleared")
    
    @log_function_call()
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from disk cache.
        
        Returns:
            Number of entries removed
        """
        removed = 0
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    timestamp = data['timestamp']
                
                if self._is_expired(timestamp):
                    cache_file.unlink()
                    removed += 1
                    
            except Exception as e:
                logger.error(f"Error checking {cache_file}: {e}")
                # Remove corrupted files
                cache_file.unlink(missing_ok=True)
                removed += 1
        
        logger.info(f"Cleanup removed {removed} expired entries")
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            disk_files = len(list(self.cache_dir.glob("*.cache")))
            
            return {
                'memory_entries': len(self._memory_cache),
                'disk_entries': disk_files,
                'total_hits': self._stats['hits'],
                'total_misses': self._stats['misses'],
                'memory_hits': self._stats['memory_hits'],
                'disk_hits': self._stats['disk_hits'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self._stats['evictions']
            }


# Global cache instance
_global_cache: Optional[ContentCache] = None


def get_cache() -> ContentCache:
    """
    Get global cache instance (singleton pattern).
    
    Returns:
        ContentCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = ContentCache()
    
    return _global_cache


if __name__ == "__main__":
    # Example usage
    logger.info("ContentCache module loaded")
    
    # Create cache
    cache = ContentCache(cache_dir=".test_cache")
    
    # Store content
    cache.set("Generate chapter about AI", "Chapter content here...")
    
    # Retrieve content
    content = cache.get("Generate chapter about AI")
    print(f"Retrieved: {content}")
    
    # Get statistics
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
