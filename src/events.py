"""
Event System for Multi-Agent Scheduler

Provides pub-sub event bus for decoupled component communication.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """Event data structure"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None


class EventBus:
    """
    Event bus for publish-subscribe pattern

    Features:
    - Async event handling
    - Multiple listeners per event
    - Wildcard subscriptions
    - Event history

    Example:
        >>> bus = EventBus()
        >>> async def on_task_start(event):
        >>>     print(f"Task started: {event.data}")
        >>> bus.on('task.started', on_task_start)
        >>> await bus.emit('task.started', {'task_id': 'task1'})
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize event bus

        Args:
            max_history: Maximum events to keep in history
        """
        self.listeners: Dict[str, List[Callable]] = {}
        self.history: List[Event] = []
        self.max_history = max_history

    def on(self, event_type: str, callback: Callable) -> None:
        """
        Register event listener

        Args:
            event_type: Event type to listen for
            callback: Async callback function

        Example:
            >>> async def handler(event):
            >>>     print(event.data)
            >>> bus.on('task.completed', handler)
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def off(self, event_type: str, callback: Optional[Callable] = None) -> None:
        """
        Unregister event listener

        Args:
            event_type: Event type
            callback: Specific callback to remove (None = remove all)
        """
        if event_type not in self.listeners:
            return

        if callback is None:
            del self.listeners[event_type]
        else:
            self.listeners[event_type] = [
                cb for cb in self.listeners[event_type]
                if cb != callback
            ]

    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None
    ) -> None:
        """
        Emit event to all listeners

        Args:
            event_type: Event type
            data: Event data
            source: Event source (optional)

        Example:
            >>> await bus.emit('task.started', {'task_id': 'task1'})
        """
        # Create event
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )

        # Add to history
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Call listeners
        if event_type in self.listeners:
            await asyncio.gather(*[
                callback(event)
                for callback in self.listeners[event_type]
            ], return_exceptions=True)

    def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Event]:
        """
        Get event history

        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum events to return

        Returns:
            List of events
        """
        events = self.history
        if event_type:
            events = [e for e in events if e.type == event_type]

        return events[-limit:]


# Global event bus
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global EventBus instance"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


# Event type constants
class Events:
    """Standard event types"""
    TASK_STARTED = 'task.started'
    TASK_COMPLETED = 'task.completed'
    TASK_FAILED = 'task.failed'
    BATCH_STARTED = 'batch.started'
    BATCH_COMPLETED = 'batch.completed'
    AGENT_SELECTED = 'agent.selected'
    WORKSPACE_CREATED = 'workspace.created'
