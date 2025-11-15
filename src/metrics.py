"""
Metrics Collection System

Provides real-time performance monitoring and statistics collection.
"""

import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from contextlib import contextmanager


class Timer:
    """Context manager for timing code blocks"""

    def __init__(self, name: str, collector: 'MetricsCollector'):
        self.name = name
        self.collector = collector
        self.start_time: Optional[float] = None

    def __enter__(self) -> 'Timer':
        self.start_time = time.time()
        return self

    def __exit__(self, *args) -> None:
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_time(self.name, duration)


class MetricsCollector:
    """
    Metrics collector for performance monitoring

    Features:
    - Counter metrics
    - Timing metrics
    - Aggregated statistics
    - Real-time reporting

    Example:
        >>> metrics = MetricsCollector()
        >>> metrics.inc('tasks.completed')
        >>> with metrics.time('task.execution'):
        >>>     # Do work
        >>>     pass
        >>> stats = metrics.get_stats()
    """

    def __init__(self):
        """Initialize metrics collector"""
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = {}

    def inc(self, name: str, value: int = 1) -> None:
        """
        Increment counter

        Args:
            name: Counter name
            value: Increment value (default: 1)

        Example:
            >>> metrics.inc('api.calls')
            >>> metrics.inc('tokens.used', 100)
        """
        self.counters[name] += value

    def dec(self, name: str, value: int = 1) -> None:
        """
        Decrement counter

        Args:
            name: Counter name
            value: Decrement value (default: 1)
        """
        self.counters[name] -= value

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set gauge value

        Args:
            name: Gauge name
            value: Current value

        Example:
            >>> metrics.set_gauge('queue.size', 10)
        """
        self.gauges[name] = value

    def record_time(self, name: str, duration: float) -> None:
        """
        Record timing

        Args:
            name: Timer name
            duration: Duration in seconds
        """
        self.timers[name].append(duration)

    @contextmanager
    def time(self, name: str):
        """
        Context manager for timing

        Args:
            name: Timer name

        Example:
            >>> with metrics.time('task.execution'):
            >>>     # Code to time
            >>>     pass
        """
        timer = Timer(name, self)
        with timer:
            yield timer

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics

        Returns:
            Dictionary with all metrics and statistics
        """
        stats: Dict[str, Any] = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {}
        }

        # Calculate timer statistics
        for name, values in self.timers.items():
            if values:
                stats['timers'][name] = {
                    'count': len(values),
                    'total': sum(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p50': self._percentile(values, 0.5),
                    'p95': self._percentile(values, 0.95),
                    'p99': self._percentile(values, 0.99),
                }

        return stats

    def _percentile(self, values: List[float], p: float) -> float:
        """
        Calculate percentile

        Args:
            values: List of values
            p: Percentile (0-1)

        Returns:
            Percentile value
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * p
        f = int(k)
        c = f + 1

        if c >= len(sorted_values):
            return sorted_values[-1]

        # Linear interpolation
        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)
        return d0 + d1

    def print_stats(self) -> None:
        """Print formatted statistics"""
        stats = self.get_stats()

        print("\n=== Metrics Statistics ===")

        if stats['counters']:
            print("\nCounters:")
            for name, value in stats['counters'].items():
                print(f"  {name}: {value}")

        if stats['gauges']:
            print("\nGauges:")
            for name, value in stats['gauges'].items():
                print(f"  {name}: {value:.2f}")

        if stats['timers']:
            print("\nTimers:")
            for name, timer_stats in stats['timers'].items():
                print(f"  {name}:")
                print(f"    Count: {timer_stats['count']}")
                print(f"    Total: {timer_stats['total']:.2f}s")
                print(f"    Avg: {timer_stats['avg']:.2f}s")
                print(f"    Min: {timer_stats['min']:.2f}s")
                print(f"    Max: {timer_stats['max']:.2f}s")
                print(f"    P95: {timer_stats['p95']:.2f}s")

    def reset(self) -> None:
        """Reset all metrics"""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()


# Global metrics instance
_global_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global MetricsCollector instance"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics


# Example usage
if __name__ == "__main__":
    # Test metrics
    metrics = MetricsCollector()

    # Counter
    metrics.inc('tasks.completed')
    metrics.inc('tasks.completed')
    metrics.inc('tokens.used', 150)

    # Gauge
    metrics.set_gauge('queue.size', 5)

    # Timer
    with metrics.time('task.execution'):
        time.sleep(0.1)

    with metrics.time('task.execution'):
        time.sleep(0.2)

    metrics.print_stats()
