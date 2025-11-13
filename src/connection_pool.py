"""
Agent Connection Pool

Manages reusable AI agent connections to improve performance
and reduce overhead from creating new connections.
"""

from typing import Dict, Optional, Any
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI


class AgentConnectionPool:
    """
    Connection pool for AI agents

    Features:
    - Singleton pattern for connection reuse
    - Lazy initialization
    - Connection validation
    - Statistics tracking

    Example:
        >>> pool = AgentConnectionPool.get_instance()
        >>> client = pool.get_claude_client(api_key)
        >>> # Reuses connection on subsequent calls with same key
    """

    _instance: Optional['AgentConnectionPool'] = None
    _claude_clients: Dict[str, AsyncAnthropic] = {}
    _openai_clients: Dict[str, AsyncOpenAI] = {}
    _stats: Dict[str, Any] = {
        'claude_connections': 0,
        'openai_connections': 0,
        'claude_reuses': 0,
        'openai_reuses': 0
    }

    def __init__(self) -> None:
        """Initialize connection pool (use get_instance() instead)"""
        self._claude_clients = {}
        self._openai_clients = {}
        self._stats = {
            'claude_connections': 0,
            'openai_connections': 0,
            'claude_reuses': 0,
            'openai_reuses': 0
        }

    @classmethod
    def get_instance(cls) -> 'AgentConnectionPool':
        """
        Get singleton instance of connection pool

        Returns:
            Global AgentConnectionPool instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_claude_client(
        self,
        api_key: str,
        **kwargs: Any
    ) -> AsyncAnthropic:
        """
        Get or create Claude client from pool

        Args:
            api_key: Anthropic API key
            **kwargs: Additional client options

        Returns:
            AsyncAnthropic client instance
        """
        # Create cache key from api_key hash
        cache_key = self._hash_key(api_key)

        if cache_key in self._claude_clients:
            self._stats['claude_reuses'] += 1
            return self._claude_clients[cache_key]

        # Create new client
        client = AsyncAnthropic(api_key=api_key, **kwargs)
        self._claude_clients[cache_key] = client
        self._stats['claude_connections'] += 1

        return client

    def get_openai_client(
        self,
        api_key: str,
        **kwargs: Any
    ) -> AsyncOpenAI:
        """
        Get or create OpenAI client from pool

        Args:
            api_key: OpenAI API key
            **kwargs: Additional client options

        Returns:
            AsyncOpenAI client instance
        """
        # Create cache key from api_key hash
        cache_key = self._hash_key(api_key)

        if cache_key in self._openai_clients:
            self._stats['openai_reuses'] += 1
            return self._openai_clients[cache_key]

        # Create new client
        client = AsyncOpenAI(api_key=api_key, **kwargs)
        self._openai_clients[cache_key] = client
        self._stats['openai_connections'] += 1

        return client

    def _hash_key(self, api_key: str) -> str:
        """
        Create hash of API key for cache lookup

        Args:
            api_key: API key to hash

        Returns:
            Hash string
        """
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics

        Returns:
            Dictionary with pool statistics
        """
        return {
            **self._stats,
            'claude_pool_size': len(self._claude_clients),
            'openai_pool_size': len(self._openai_clients),
            'total_pool_size': len(self._claude_clients) + len(self._openai_clients)
        }

    def clear(self) -> None:
        """Clear all pooled connections"""
        self._claude_clients.clear()
        self._openai_clients.clear()
        self._stats = {
            'claude_connections': 0,
            'openai_connections': 0,
            'claude_reuses': 0,
            'openai_reuses': 0
        }

    def print_stats(self) -> None:
        """Print connection pool statistics"""
        stats = self.get_stats()
        print("\n=== Connection Pool Statistics ===")
        print(f"Claude connections: {stats['claude_connections']}")
        print(f"Claude reuses: {stats['claude_reuses']}")
        print(f"OpenAI connections: {stats['openai_connections']}")
        print(f"OpenAI reuses: {stats['openai_reuses']}")
        print(f"Total pool size: {stats['total_pool_size']}")

        if stats['claude_connections'] > 0:
            reuse_rate = stats['claude_reuses'] / (stats['claude_connections'] + stats['claude_reuses']) * 100
            print(f"Claude reuse rate: {reuse_rate:.1f}%")

        if stats['openai_connections'] > 0:
            reuse_rate = stats['openai_reuses'] / (stats['openai_connections'] + stats['openai_reuses']) * 100
            print(f"OpenAI reuse rate: {reuse_rate:.1f}%")


# Convenience functions
def get_pooled_claude_client(api_key: str, **kwargs: Any) -> AsyncAnthropic:
    """
    Get Claude client from global pool

    Args:
        api_key: Anthropic API key
        **kwargs: Additional client options

    Returns:
        AsyncAnthropic client instance
    """
    return AgentConnectionPool.get_instance().get_claude_client(api_key, **kwargs)


def get_pooled_openai_client(api_key: str, **kwargs: Any) -> AsyncOpenAI:
    """
    Get OpenAI client from global pool

    Args:
        api_key: OpenAI API key
        **kwargs: Additional client options

    Returns:
        AsyncOpenAI client instance
    """
    return AgentConnectionPool.get_instance().get_openai_client(api_key, **kwargs)


# Example usage
if __name__ == "__main__":
    # Test connection pool
    pool = AgentConnectionPool.get_instance()

    # Simulate multiple clients with same key
    test_key = "test-key-123"

    client1 = pool.get_claude_client(test_key)
    client2 = pool.get_claude_client(test_key)  # Should reuse

    assert client1 is client2, "Should reuse same client"

    pool.print_stats()
