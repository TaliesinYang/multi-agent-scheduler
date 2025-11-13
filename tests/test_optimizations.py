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


class TestComplexityAnalyzer:
    """Test complexity analyzer"""

    def test_basic_analysis(self):
        """Test basic complexity analysis"""
        from src.complexity_analyzer import ComplexityAnalyzer

        analyzer = ComplexityAnalyzer()

        # Simple task
        score = analyzer.analyze("Fix typo in README")
        assert score.level == 'trivial' or score.level == 'low'
        assert score.score < 20

        # Complex task
        score = analyzer.analyze(
            "Build a full-stack e-commerce platform with React, Node.js, "
            "PostgreSQL, authentication, and payment integration"
        )
        assert score.level in ['high', 'very_high']
        assert score.score > 50

    def test_keyword_detection(self):
        """Test keyword-based scoring"""
        from src.complexity_analyzer import ComplexityAnalyzer

        analyzer = ComplexityAnalyzer()

        # Task with high-complexity keywords
        score1 = analyzer.analyze("Build microservices with authentication and database")
        score2 = analyzer.analyze("Update README file")

        assert score1.score > score2.score

    def test_task_range(self):
        """Test recommended task range"""
        from src.complexity_analyzer import ComplexityAnalyzer

        analyzer = ComplexityAnalyzer()

        # Simple task
        min_tasks, max_tasks = analyzer.get_task_range("Fix bug")
        assert min_tasks <= max_tasks
        assert min_tasks < 10

        # Complex task
        min_tasks, max_tasks = analyzer.get_task_range(
            "Build enterprise application with microservices and CI/CD"
        )
        assert min_tasks > 15


class TestDependencyInjection:
    """Test dependency injection system"""

    def test_service_registration(self):
        """Test service registration and retrieval"""
        from src.dependency_injection import ServiceContainer

        container = ServiceContainer()

        class MockService:
            def do_something(self):
                return "done"

        service = MockService()
        container.register('test_service', service)

        retrieved = container.get('test_service')
        assert retrieved is service
        assert retrieved.do_something() == "done"

    def test_factory_pattern(self):
        """Test factory registration"""
        from src.dependency_injection import ServiceContainer

        container = ServiceContainer()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"

        container.register_singleton('service', factory)

        # Get twice - should be same instance
        instance1 = container.get('service')
        instance2 = container.get('service')

        assert instance1 == instance2
        assert call_count == 1

    def test_scheduler_dependencies(self):
        """Test SchedulerDependencies bundle"""
        from src.dependency_injection import SchedulerDependencies

        class MockAgent:
            def __init__(self, name):
                self.name = name

        agents = {'claude': MockAgent('claude')}
        deps = SchedulerDependencies(agents=agents)

        assert deps.agents == agents
        assert deps.get_logger() is None  # No logger provided
        assert deps.get_config() is not None  # Should create default


class TestPluginSystem:
    """Test plugin system"""

    def test_plugin_registration(self):
        """Test plugin registration"""
        from src.plugin_system import PluginManager, Plugin, PluginMetadata, PluginHook

        manager = PluginManager()

        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_plugin",
                    version="1.0.0",
                    hooks=[PluginHook.BEFORE_TASK]
                )

            async def on_hook(self, hook, context):
                return None

        plugin = TestPlugin()
        manager.register(plugin)

        assert 'test_plugin' in manager.plugins
        assert manager.enabled_plugins['test_plugin'] is True

    @pytest.mark.asyncio
    async def test_hook_execution(self):
        """Test hook execution"""
        from src.plugin_system import PluginManager, Plugin, PluginMetadata, PluginHook

        manager = PluginManager()
        hook_called = []

        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata(
                    name="test_plugin",
                    version="1.0.0",
                    hooks=[PluginHook.BEFORE_TASK]
                )

            async def on_hook(self, hook, context):
                hook_called.append(hook)
                return {'modified': True}

        plugin = TestPlugin()
        manager.register(plugin)

        context = {'task_id': 'task1'}
        result = await manager.execute_hook(PluginHook.BEFORE_TASK, context)

        assert len(hook_called) == 1
        assert result['modified'] is True

    def test_plugin_enable_disable(self):
        """Test plugin enable/disable"""
        from src.plugin_system import PluginManager, Plugin, PluginMetadata

        manager = PluginManager()

        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata(name="test_plugin", version="1.0.0")

            async def on_hook(self, hook, context):
                return None

        plugin = TestPlugin()
        manager.register(plugin)

        assert manager.enabled_plugins['test_plugin'] is True

        manager.disable_plugin('test_plugin')
        assert manager.enabled_plugins['test_plugin'] is False

        manager.enable_plugin('test_plugin')
        assert manager.enabled_plugins['test_plugin'] is True


class TestWorkspaceLock:
    """Test workspace file locking and sandboxing"""

    @pytest.mark.asyncio
    async def test_file_lock(self):
        """Test basic file locking"""
        from src.workspace_lock import FileLock

        lock = FileLock()

        # Lock should work
        async with lock.acquire('/tmp/test_file.txt'):
            assert lock.is_locked('/tmp/test_file.txt')

        # Should be unlocked after context
        assert not lock.is_locked('/tmp/test_file.txt')

    @pytest.mark.asyncio
    async def test_sandboxed_workspace(self):
        """Test sandboxed workspace manager"""
        from src.workspace_lock import SandboxedWorkspaceManager
        import tempfile
        import shutil

        # Use temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            manager = SandboxedWorkspaceManager(base_dir=temp_dir)

            # Create workspace
            workspace = await manager.create_workspace('test_project')
            assert workspace.exists()

            # Write file
            test_file = workspace / 'test.txt'
            await manager.write_file(test_file, 'Hello, world!')

            # Read file
            content = await manager.read_file(test_file)
            assert content == 'Hello, world!'

            # Get workspace info
            info = manager.get_workspace_info(workspace)
            assert info['file_count'] == 1
            assert info['total_size'] > 0

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_path_validation(self):
        """Test path validation and security"""
        from src.workspace_lock import SandboxedWorkspaceManager
        from pathlib import Path
        import tempfile

        temp_dir = tempfile.mkdtemp()

        try:
            manager = SandboxedWorkspaceManager(base_dir=temp_dir)

            # Should reject path outside sandbox
            with pytest.raises(PermissionError):
                await manager.write_file(Path('/etc/passwd'), 'bad content')

            # Should reject path traversal
            with pytest.raises(PermissionError):
                await manager.write_file(Path(temp_dir) / '..' / '..' / 'escape.txt', 'content')

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
