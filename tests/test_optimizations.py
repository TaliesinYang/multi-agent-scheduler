"""
Tests for optimization modules

Tests new features:
- Security (API key encryption)
- Connection pool
- Result cache
- Events
- Metrics
- Input validation
- Configuration management
"""

import pytest
import asyncio
import time
from pathlib import Path


class TestSecurity:
    """Test security module"""

    def test_key_manager_basic(self):
        """Test basic key storage and retrieval"""
        from src.security import SecureKeyManager

        manager = SecureKeyManager(master_password='test-password-123')

        # Store key
        manager.set_key('TEST_KEY', 'test-value-456')

        # Retrieve key
        value = manager.get_key('TEST_KEY')
        assert value == 'test-value-456'

        # Delete key
        manager.delete_key('TEST_KEY')
        value = manager.get_key('TEST_KEY')
        assert value is None


class TestConnectionPool:
    """Test connection pool"""

    def test_pool_reuse(self):
        """Test connection reuse"""
        from src.connection_pool import AgentConnectionPool

        pool = AgentConnectionPool()
        test_key = 'test-api-key-789'

        # Get client twice
        client1 = pool.get_claude_client(test_key)
        client2 = pool.get_claude_client(test_key)

        # Should be same instance
        assert client1 is client2

        # Check stats
        stats = pool.get_stats()
        assert stats['claude_connections'] == 1
        assert stats['claude_reuses'] == 1


class TestResultCache:
    """Test result cache"""

    def test_cache_hit_miss(self):
        """Test cache hit and miss"""
        from src.cache import ResultCache

        cache = ResultCache(max_size=10, ttl=0)

        # Cache miss
        result = cache.get('prompt1')
        assert result is None

        # Set value
        cache.set('prompt1', {'result': 'answer1'})

        # Cache hit
        result = cache.get('prompt1')
        assert result == {'result': 'answer1'}

        # Check stats
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_cache_eviction(self):
        """Test LRU eviction"""
        from src.cache import ResultCache

        cache = ResultCache(max_size=2, ttl=0)

        # Add 3 items (should evict first)
        cache.set('prompt1', {'result': 'answer1'})
        cache.set('prompt2', {'result': 'answer2'})
        cache.set('prompt3', {'result': 'answer3'})

        # First should be evicted
        result = cache.get('prompt1')
        assert result is None

        # Others should still be there
        result = cache.get('prompt2')
        assert result == {'result': 'answer2'}


class TestEvents:
    """Test event system"""

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test event emission and handling"""
        from src.events import EventBus

        bus = EventBus()
        received_events = []

        # Register listener
        async def handler(event):
            received_events.append(event)

        bus.on('test.event', handler)

        # Emit event
        await bus.emit('test.event', {'data': 'value'})

        # Check event was received
        assert len(received_events) == 1
        assert received_events[0].type == 'test.event'
        assert received_events[0].data == {'data': 'value'}


class TestMetrics:
    """Test metrics collection"""

    def test_counters(self):
        """Test counter metrics"""
        from src.metrics import MetricsCollector

        metrics = MetricsCollector()

        # Increment counters
        metrics.inc('test.counter')
        metrics.inc('test.counter')
        metrics.inc('test.counter', 5)

        # Check stats
        stats = metrics.get_stats()
        assert stats['counters']['test.counter'] == 7

    def test_timers(self):
        """Test timer metrics"""
        from src.metrics import MetricsCollector

        metrics = MetricsCollector()

        # Record times
        with metrics.time('test.operation'):
            time.sleep(0.01)

        with metrics.time('test.operation'):
            time.sleep(0.02)

        # Check stats
        stats = metrics.get_stats()
        timer_stats = stats['timers']['test.operation']
        assert timer_stats['count'] == 2
        assert timer_stats['min'] >= 0.01
        assert timer_stats['max'] >= 0.02


class TestValidation:
    """Test input validation"""

    def test_prompt_validation(self):
        """Test prompt validation"""
        from src.validation import InputValidator

        validator = InputValidator()

        # Valid prompt
        is_valid, error = validator.validate_prompt("Hello world")
        assert is_valid

        # Dangerous prompt
        is_valid, error = validator.validate_prompt("Run: rm -rf /")
        assert not is_valid
        assert 'dangerous pattern' in error.lower()

        # Too long prompt
        is_valid, error = validator.validate_prompt("x" * 100000)
        assert not is_valid
        assert 'too long' in error.lower()

    def test_path_validation(self):
        """Test workspace path validation"""
        from src.validation import InputValidator

        validator = InputValidator()

        # Valid path
        is_valid, error = validator.validate_workspace_path("/tmp/workspace")
        assert is_valid

        # Path traversal
        is_valid, error = validator.validate_workspace_path("../../../etc/passwd")
        assert not is_valid

        # Sensitive path
        is_valid, error = validator.validate_workspace_path("/etc/shadow")
        assert not is_valid


class TestConfigManager:
    """Test configuration management"""

    def test_get_defaults(self):
        """Test getting default values"""
        from src.config_manager import ConfigManager

        config = ConfigManager()

        # Get default value
        max_tasks = config.get('scheduler.max_tasks')
        assert max_tasks == 50

        # Get with custom default
        value = config.get('nonexistent.key', default=100)
        assert value == 100

    def test_set_get(self):
        """Test setting and getting values"""
        from src.config_manager import ConfigManager

        config = ConfigManager()

        # Set value
        config.set('custom.setting', 'test-value')

        # Get value
        value = config.get('custom.setting')
        assert value == 'test-value'


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
