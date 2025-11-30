"""
Cache module for AI content caching.

Provides utilities for caching AI-generated content to reduce API costs.
"""

from .content_cache import ContentCache, get_cache

__all__ = ['ContentCache', 'get_cache']
