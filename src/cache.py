"""
Result Caching System

Provides LRU cache for AI agent responses to avoid redundant API calls.
"""

import hashlib
import json
import time
from typing import Dict, Optional, Any
from collections import OrderedDict


class ResultCache:
    """
    LRU cache for AI agent results

    Features:
    - LRU eviction policy
    - TTL (time-to-live) support
    - Hit/miss statistics
    - Size limits

    Example:
        >>> cache = ResultCache(max_size=100, ttl=3600)
        >>> cache.set('prompt1', {'result': 'answer'})
        >>> result = cache.get('prompt1')
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize result cache

        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

    def _make_key(self, prompt: str, agent_type: str = '', **kwargs: Any) -> str:
        """
        Create cache key from prompt and parameters

        Args:
            prompt: Input prompt
            agent_type: Agent type (optional)
            **kwargs: Additional parameters

        Returns:
            Cache key hash
        """
        # Combine prompt, agent type, and kwargs for key
        key_data = {
            'prompt': prompt,
            'agent_type': agent_type,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        agent_type: str = '',
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result

        Args:
            prompt: Input prompt
            agent_type: Agent type
            **kwargs: Additional parameters

        Returns:
            Cached result or None if not found/expired
        """
        key = self._make_key(prompt, agent_type, **kwargs)

        if key not in self.cache:
            self.stats['misses'] += 1
            return None

        # Check TTL
        entry = self.cache[key]
        if self.ttl > 0:
            age = time.time() - entry['timestamp']
            if age > self.ttl:
                # Expired
                del self.cache[key]
                self.stats['misses'] += 1
                self.stats['expirations'] += 1
                return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.stats['hits'] += 1

        return entry['data']

    def set(
        self,
        prompt: str,
        result: Dict[str, Any],
        agent_type: str = '',
        **kwargs: Any
    ) -> None:
        """
        Store result in cache

        Args:
            prompt: Input prompt
            result: Result to cache
            agent_type: Agent type
            **kwargs: Additional parameters
        """
        key = self._make_key(prompt, agent_type, **kwargs)

        # Evict oldest if at capacity
        if key not in self.cache and len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # Remove oldest (FIFO)
            self.stats['evictions'] += 1

        # Store with timestamp
        self.cache[key] = {
            'data': result,
            'timestamp': time.time()
        }

        # Move to end
        self.cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cached results"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def print_stats(self) -> None:
        """Print cache statistics"""
        stats = self.get_stats()
        print("\n=== Cache Statistics ===")
        print(f"Size: {stats['size']}/{stats['max_size']}")
        print(f"Hits: {stats['hits']}")
        print(f"Misses: {stats['misses']}")
        print(f"Hit rate: {stats['hit_rate']:.1f}%")
        print(f"Evictions: {stats['evictions']}")
        print(f"Expirations: {stats['expirations']}")


# Global cache instance
_global_cache: Optional[ResultCache] = None


def get_global_cache(max_size: int = 1000, ttl: int = 3600) -> ResultCache:
    """
    Get global ResultCache instance

    Args:
        max_size: Maximum cache size
        ttl: Time-to-live in seconds

    Returns:
        Global ResultCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ResultCache(max_size=max_size, ttl=ttl)
    return _global_cache


# Convenience decorator
def cached_agent_call(agent_type: str = ''):
    """
    Decorator to cache agent call results

    Args:
        agent_type: Agent type identifier

    Example:
        >>> @cached_agent_call(agent_type='claude')
        >>> async def call_claude(prompt):
        >>>     return await claude.call(prompt)
    """
    def decorator(func):
        async def wrapper(prompt: str, *args, **kwargs):
            cache = get_global_cache()

            # Try to get from cache
            cached_result = cache.get(prompt, agent_type, **kwargs)
            if cached_result is not None:
                return cached_result

            # Call function
            result = await func(prompt, *args, **kwargs)

            # Cache result
            if isinstance(result, dict):
                cache.set(prompt, result, agent_type, **kwargs)

            return result

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Test cache
    cache = ResultCache(max_size=3, ttl=0)

    # Add items
    cache.set('prompt1', {'result': 'answer1'})
    cache.set('prompt2', {'result': 'answer2'})
    cache.set('prompt3', {'result': 'answer3'})

    # Test hit
    result = cache.get('prompt1')
    assert result == {'result': 'answer1'}

    # Test miss
    result = cache.get('prompt_unknown')
    assert result is None

    # Test eviction (adding 4th item should evict prompt2)
    cache.set('prompt4', {'result': 'answer4'})
    result = cache.get('prompt2')
    assert result is None  # Should be evicted

    cache.print_stats()
