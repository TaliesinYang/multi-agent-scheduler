"""
Plugin System

Extensible plugin architecture for the multi-agent scheduler.
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class PluginHook(Enum):
    """
    Plugin hook points

    These define when plugins can inject behavior.
    """
    # Scheduler hooks
    BEFORE_EXECUTION = "before_execution"
    AFTER_EXECUTION = "after_execution"
    BEFORE_TASK = "before_task"
    AFTER_TASK = "after_task"

    # Agent hooks
    BEFORE_AGENT_CALL = "before_agent_call"
    AFTER_AGENT_CALL = "after_agent_call"

    # Meta-agent hooks
    BEFORE_DECOMPOSITION = "before_decomposition"
    AFTER_DECOMPOSITION = "after_decomposition"

    # System hooks
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class PluginMetadata:
    """
    Plugin metadata

    Attributes:
        name: Plugin name
        version: Plugin version
        author: Plugin author
        description: Plugin description
        hooks: List of hooks this plugin uses
    """
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    hooks: List[PluginHook] = None

    def __post_init__(self):
        if self.hooks is None:
            self.hooks = []


class Plugin(ABC):
    """
    Base plugin class

    All plugins must inherit from this class and implement the required methods.

    Example:
        >>> class MyPlugin(Plugin):
        ...     def get_metadata(self):
        ...         return PluginMetadata(
        ...             name="my_plugin",
        ...             version="1.0.0",
        ...             hooks=[PluginHook.BEFORE_TASK]
        ...         )
        ...
        ...     async def on_hook(self, hook, context):
        ...         if hook == PluginHook.BEFORE_TASK:
        ...             print(f"Task starting: {context['task_id']}")
    """

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata

        Returns:
            PluginMetadata object
        """
        pass

    @abstractmethod
    async def on_hook(self, hook: PluginHook, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle hook event

        Args:
            hook: Hook type
            context: Hook context data

        Returns:
            Modified context or None
        """
        pass

    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration

        Args:
            config: Plugin configuration
        """
        pass

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass


class PluginManager:
    """
    Plugin manager

    Loads, manages, and executes plugins.

    Features:
    - Plugin discovery
    - Hook execution
    - Plugin lifecycle management
    - Dependency resolution

    Example:
        >>> manager = PluginManager()
        >>> manager.register(MyPlugin())
        >>> await manager.execute_hook(PluginHook.BEFORE_TASK, {'task_id': 'task1'})
    """

    def __init__(self):
        """Initialize plugin manager"""
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[PluginHook, List[Plugin]] = {hook: [] for hook in PluginHook}
        self.enabled_plugins: Dict[str, bool] = {}

    def register(self, plugin: Plugin, enabled: bool = True) -> None:
        """
        Register a plugin

        Args:
            plugin: Plugin instance
            enabled: Whether plugin is enabled
        """
        metadata = plugin.get_metadata()
        plugin_name = metadata.name

        if plugin_name in self.plugins:
            print(f"⚠️  Warning: Plugin '{plugin_name}' already registered, replacing")

        self.plugins[plugin_name] = plugin
        self.enabled_plugins[plugin_name] = enabled

        # Register hooks
        for hook in metadata.hooks:
            if hook not in self.hooks:
                self.hooks[hook] = []
            self.hooks[hook].append(plugin)

        print(f"✓ Registered plugin: {plugin_name} v{metadata.version}")

    def unregister(self, plugin_name: str) -> None:
        """
        Unregister a plugin

        Args:
            plugin_name: Plugin name to unregister
        """
        if plugin_name not in self.plugins:
            return

        plugin = self.plugins[plugin_name]
        metadata = plugin.get_metadata()

        # Remove from hooks
        for hook in metadata.hooks:
            if hook in self.hooks:
                self.hooks[hook] = [p for p in self.hooks[hook] if p is not plugin]

        # Remove plugin
        del self.plugins[plugin_name]
        del self.enabled_plugins[plugin_name]

        print(f"✓ Unregistered plugin: {plugin_name}")

    def enable_plugin(self, plugin_name: str) -> None:
        """
        Enable a plugin

        Args:
            plugin_name: Plugin name
        """
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins[plugin_name] = True
            print(f"✓ Enabled plugin: {plugin_name}")

    def disable_plugin(self, plugin_name: str) -> None:
        """
        Disable a plugin

        Args:
            plugin_name: Plugin name
        """
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins[plugin_name] = False
            print(f"✓ Disabled plugin: {plugin_name}")

    async def execute_hook(
        self,
        hook: PluginHook,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute hook on all registered plugins

        Args:
            hook: Hook to execute
            context: Hook context

        Returns:
            Modified context
        """
        if hook not in self.hooks:
            return context

        for plugin in self.hooks[hook]:
            metadata = plugin.get_metadata()

            # Skip disabled plugins
            if not self.enabled_plugins.get(metadata.name, True):
                continue

            try:
                result = await plugin.on_hook(hook, context)
                if result is not None:
                    context.update(result)
            except Exception as e:
                print(f"❌ Plugin '{metadata.name}' error on hook {hook.value}: {e}")

        return context

    async def initialize_plugins(self, config: Dict[str, Any]) -> None:
        """
        Initialize all plugins

        Args:
            config: Global configuration
        """
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin_config = config.get('plugins', {}).get(plugin_name, {})
                await plugin.initialize(plugin_config)
                print(f"✓ Initialized plugin: {plugin_name}")
            except Exception as e:
                print(f"❌ Failed to initialize plugin '{plugin_name}': {e}")

    async def cleanup_plugins(self) -> None:
        """Cleanup all plugins"""
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.cleanup()
            except Exception as e:
                print(f"❌ Failed to cleanup plugin '{plugin_name}': {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all registered plugins

        Returns:
            List of plugin information dictionaries
        """
        plugins_info = []

        for plugin_name, plugin in self.plugins.items():
            metadata = plugin.get_metadata()
            plugins_info.append({
                'name': metadata.name,
                'version': metadata.version,
                'author': metadata.author,
                'description': metadata.description,
                'enabled': self.enabled_plugins.get(plugin_name, True),
                'hooks': [hook.value for hook in metadata.hooks]
            })

        return plugins_info

    def load_from_directory(self, directory: str) -> int:
        """
        Load plugins from directory

        Args:
            directory: Directory path containing plugin files

        Returns:
            Number of plugins loaded
        """
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            print(f"⚠️  Plugin directory not found: {directory}")
            return 0

        loaded_count = 0

        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                # Import module
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find Plugin subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, Plugin) and
                        obj is not Plugin):

                        # Instantiate and register
                        plugin_instance = obj()
                        self.register(plugin_instance)
                        loaded_count += 1

            except Exception as e:
                print(f"❌ Failed to load plugin from {plugin_file}: {e}")

        print(f"✓ Loaded {loaded_count} plugins from {directory}")
        return loaded_count


# Global plugin manager
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


# ==============================================================================
# Example Plugins
# ==============================================================================


class LoggingPlugin(Plugin):
    """
    Example plugin that logs all hooks

    Demonstrates basic plugin structure.
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="logging_plugin",
            version="1.0.0",
            author="Multi-Agent Scheduler",
            description="Logs all hook executions",
            hooks=[
                PluginHook.BEFORE_TASK,
                PluginHook.AFTER_TASK,
                PluginHook.BEFORE_EXECUTION,
                PluginHook.AFTER_EXECUTION,
            ]
        )

    async def on_hook(self, hook: PluginHook, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log hook execution"""
        print(f"[LoggingPlugin] Hook: {hook.value}, Context: {list(context.keys())}")
        return None


class MetricsPlugin(Plugin):
    """
    Example plugin that collects metrics

    Tracks task execution counts and timing.
    """

    def __init__(self):
        self.task_count = 0
        self.execution_count = 0

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics_plugin",
            version="1.0.0",
            author="Multi-Agent Scheduler",
            description="Collects execution metrics",
            hooks=[
                PluginHook.BEFORE_TASK,
                PluginHook.AFTER_TASK,
                PluginHook.AFTER_EXECUTION,
            ]
        )

    async def on_hook(self, hook: PluginHook, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect metrics"""
        if hook == PluginHook.BEFORE_TASK:
            self.task_count += 1

        elif hook == PluginHook.AFTER_EXECUTION:
            self.execution_count += 1
            print(f"[MetricsPlugin] Total tasks: {self.task_count}, "
                  f"Executions: {self.execution_count}")

        return None


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        # Create plugin manager
        manager = PluginManager()

        # Register example plugins
        manager.register(LoggingPlugin())
        manager.register(MetricsPlugin())

        # List plugins
        print("\nRegistered Plugins:")
        for plugin_info in manager.list_plugins():
            print(f"  - {plugin_info['name']} v{plugin_info['version']}")
            print(f"    Enabled: {plugin_info['enabled']}")
            print(f"    Hooks: {', '.join(plugin_info['hooks'])}")

        # Execute hooks
        print("\nExecuting Hooks:")

        await manager.execute_hook(PluginHook.BEFORE_EXECUTION, {
            'mode': 'parallel'
        })

        await manager.execute_hook(PluginHook.BEFORE_TASK, {
            'task_id': 'task1',
            'agent': 'claude'
        })

        await manager.execute_hook(PluginHook.AFTER_TASK, {
            'task_id': 'task1',
            'success': True
        })

        await manager.execute_hook(PluginHook.AFTER_EXECUTION, {
            'total_time': 5.2
        })

        print("\n✓ Plugin system test completed")

    asyncio.run(test())
