"""
Dependency Injection Container

Provides dependency management for the multi-agent scheduler.
"""

from typing import Dict, Any, Optional, Protocol, Type, Callable
from dataclasses import dataclass


# ==============================================================================
# Service Protocols (Interfaces)
# ==============================================================================


class ILogger(Protocol):
    """Logger interface"""

    def log_task_start(
        self,
        task_id: str,
        prompt: str,
        agent_name: str,
        batch: int = 0,
        rationale: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log task start"""
        ...

    def log_task_complete(
        self,
        task_id: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        result: Optional[str] = None
    ) -> None:
        """Log task completion"""
        ...


class IAgentSelector(Protocol):
    """Agent selector interface"""

    def select(self, task: Any, agents: Dict[str, Any]) -> str:
        """Select best agent for task"""
        ...

    def get_last_selection_rationale(self) -> Dict[str, Any]:
        """Get rationale for last selection"""
        ...


class IMetricsCollector(Protocol):
    """Metrics collector interface"""

    def inc(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        ...

    def time(self, name: str) -> Any:
        """Time operation"""
        ...


class IEventBus(Protocol):
    """Event bus interface"""

    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None
    ) -> None:
        """Emit event"""
        ...


class ICache(Protocol):
    """Cache interface"""

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set cached value"""
        ...


# ==============================================================================
# Service Container
# ==============================================================================


class ServiceContainer:
    """
    Dependency Injection Container

    Manages service instances and provides dependency resolution.

    Features:
    - Singleton pattern for services
    - Lazy initialization
    - Factory support
    - Optional dependencies

    Example:
        >>> container = ServiceContainer()
        >>> container.register('logger', logger_instance)
        >>> logger = container.get('logger')
    """

    def __init__(self):
        """Initialize service container"""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        """
        Register service instance

        Args:
            name: Service name
            instance: Service instance
        """
        self._services[name] = instance

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register service factory

        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self._factories[name] = factory

    def register_singleton(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register singleton service

        Args:
            name: Service name
            factory: Factory function that creates the service (called once)
        """
        self._factories[name] = factory

    def get(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get service by name

        Args:
            name: Service name
            default: Default value if service not found

        Returns:
            Service instance or default
        """
        # Check if already instantiated
        if name in self._services:
            return self._services[name]

        # Check if singleton already created
        if name in self._singletons:
            return self._singletons[name]

        # Check if factory exists
        if name in self._factories:
            instance = self._factories[name]()

            # Store as singleton
            self._singletons[name] = instance
            return instance

        # Not found, return default
        return default

    def has(self, name: str) -> bool:
        """
        Check if service exists

        Args:
            name: Service name

        Returns:
            True if service exists
        """
        return (
            name in self._services or
            name in self._factories or
            name in self._singletons
        )

    def clear(self) -> None:
        """Clear all services (useful for testing)"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# ==============================================================================
# Scheduler Dependencies
# ==============================================================================


@dataclass
class SchedulerDependencies:
    """
    Scheduler dependencies bundle

    Encapsulates all dependencies needed by the scheduler.

    Example:
        >>> deps = SchedulerDependencies(
        ...     agents={'claude': claude_agent},
        ...     logger=execution_logger,
        ...     config=agent_config
        ... )
        >>> scheduler = MultiAgentScheduler(deps)
    """

    agents: Dict[str, Any]
    logger: Optional[ILogger] = None
    config: Optional[Any] = None
    agent_selector: Optional[IAgentSelector] = None
    metrics: Optional[IMetricsCollector] = None
    event_bus: Optional[IEventBus] = None
    cache: Optional[ICache] = None

    def get_logger(self) -> Optional[ILogger]:
        """Get logger or None"""
        return self.logger

    def get_config(self) -> Any:
        """Get config, loading default if needed"""
        if self.config is None:
            from src.config import AgentConfig
            self.config = AgentConfig.load()
        return self.config

    def get_agent_selector(self) -> IAgentSelector:
        """Get agent selector, creating default if needed"""
        if self.agent_selector is None:
            from src.agent_selector import SmartAgentSelector
            config = self.get_config()
            self.agent_selector = SmartAgentSelector(config)
        return self.agent_selector

    def get_metrics(self) -> Optional[IMetricsCollector]:
        """Get metrics collector or None"""
        return self.metrics

    def get_event_bus(self) -> Optional[IEventBus]:
        """Get event bus or None"""
        return self.event_bus

    def get_cache(self) -> Optional[ICache]:
        """Get cache or None"""
        return self.cache


# ==============================================================================
# Global Container
# ==============================================================================

_global_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get global service container"""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def configure_container(
    logger: Optional[ILogger] = None,
    metrics: Optional[IMetricsCollector] = None,
    event_bus: Optional[IEventBus] = None,
    cache: Optional[ICache] = None
) -> ServiceContainer:
    """
    Configure global service container

    Args:
        logger: Logger instance
        metrics: Metrics collector
        event_bus: Event bus
        cache: Cache instance

    Returns:
        Configured container
    """
    container = get_container()

    if logger is not None:
        container.register('logger', logger)

    if metrics is not None:
        container.register('metrics', metrics)

    if event_bus is not None:
        container.register('event_bus', event_bus)

    if cache is not None:
        container.register('cache', cache)

    return container


# Example usage
if __name__ == "__main__":
    # Create container
    container = ServiceContainer()

    # Register services
    class MockLogger:
        def log(self, msg: str):
            print(f"LOG: {msg}")

    logger = MockLogger()
    container.register('logger', logger)

    # Get service
    retrieved_logger = container.get('logger')
    assert retrieved_logger is logger

    # Factory example
    counter = 0

    def create_service():
        global counter
        counter += 1
        return f"service_{counter}"

    container.register_singleton('my_service', create_service)

    # Get singleton (should be same instance)
    service1 = container.get('my_service')
    service2 = container.get('my_service')
    assert service1 == service2
    assert counter == 1

    print("✓ Dependency injection test passed")
