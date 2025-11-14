"""
Health Check and Metrics API

Provides health check endpoint and Prometheus metrics for monitoring.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from fastapi import FastAPI, Response
    from fastapi.responses import JSONResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest,
        CollectorRegistry, CONTENT_TYPE_LATEST
    )
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


# Global state for health tracking
_health_state = {
    "start_time": time.time(),
    "version": "3.0.0",
    "active_tasks": 0,
    "total_tasks": 0,
    "total_errors": 0,
    "services": {}
}


def update_health(key: str, value: Any):
    """Update health state"""
    _health_state[key] = value


def increment_tasks():
    """Increment active tasks counter"""
    _health_state["active_tasks"] += 1
    _health_state["total_tasks"] += 1


def decrement_tasks():
    """Decrement active tasks counter"""
    _health_state["active_tasks"] = max(0, _health_state["active_tasks"] - 1)


def increment_errors():
    """Increment error counter"""
    _health_state["total_errors"] += 1


def set_service_status(service: str, status: str):
    """Set service status"""
    _health_state["services"][service] = status


def get_uptime() -> float:
    """Get uptime in seconds"""
    return time.time() - _health_state["start_time"]


def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return {
        "status": "healthy" if _health_state["total_errors"] < 100 else "degraded",
        "version": _health_state["version"],
        "uptime": int(get_uptime()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_tasks": _health_state["active_tasks"],
        "total_tasks_completed": _health_state["total_tasks"] - _health_state["active_tasks"],
        "total_errors": _health_state["total_errors"],
        "services": _health_state["services"]
    }


# Prometheus Metrics
if HAS_PROMETHEUS:
    # Create registry
    registry = CollectorRegistry()

    # Task metrics
    tasks_total = Counter(
        'scheduler_tasks_total',
        'Total number of tasks executed',
        ['agent_type', 'status'],
        registry=registry
    )

    tasks_active = Gauge(
        'scheduler_tasks_active',
        'Currently active tasks',
        registry=registry
    )

    task_duration = Histogram(
        'scheduler_task_duration_seconds',
        'Task execution duration in seconds',
        ['agent_type'],
        registry=registry
    )

    # Error metrics
    errors_total = Counter(
        'scheduler_errors_total',
        'Total number of errors',
        ['error_type'],
        registry=registry
    )

    # Checkpoint metrics
    checkpoint_operations = Counter(
        'checkpoint_operations_total',
        'Total checkpoint operations',
        ['operation'],  # create, load, delete
        registry=registry
    )

    checkpoint_duration = Histogram(
        'checkpoint_duration_seconds',
        'Checkpoint operation duration',
        ['operation'],
        registry=registry
    )

    # Workflow metrics
    workflow_executions = Counter(
        'workflow_executions_total',
        'Total workflow executions',
        ['status'],
        registry=registry
    )

    workflow_nodes = Histogram(
        'workflow_nodes_executed',
        'Number of nodes executed per workflow',
        registry=registry
    )

else:
    # Dummy metrics if Prometheus not available
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, amount=1):
            pass

        def dec(self, amount=1):
            pass

        def set(self, value):
            pass

        def observe(self, value):
            pass

    tasks_total = DummyMetric()
    tasks_active = DummyMetric()
    task_duration = DummyMetric()
    errors_total = DummyMetric()
    checkpoint_operations = DummyMetric()
    checkpoint_duration = DummyMetric()
    workflow_executions = DummyMetric()
    workflow_nodes = DummyMetric()
    registry = None


# FastAPI Application
if HAS_FASTAPI:
    app = FastAPI(
        title="Multi-Agent Scheduler API",
        description="Health checks and metrics for Multi-Agent Scheduler",
        version="3.0.0"
    )

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "Multi-Agent Scheduler API", "version": "3.0.0"}

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        status = get_health_status()
        status_code = 200 if status["status"] == "healthy" else 503
        return JSONResponse(content=status, status_code=status_code)

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        if not HAS_PROMETHEUS:
            return JSONResponse(
                content={"error": "Prometheus client not installed"},
                status_code=501
            )

        # Update gauges
        tasks_active.set(_health_state["active_tasks"])

        # Generate metrics
        metrics_output = generate_latest(registry)
        return Response(
            content=metrics_output,
            media_type=CONTENT_TYPE_LATEST
        )

    @app.get("/ready")
    async def readiness():
        """Readiness check endpoint"""
        # Check if critical services are available
        services_ready = all(
            status != "error"
            for status in _health_state["services"].values()
        )

        if services_ready:
            return {"status": "ready"}
        else:
            return JSONResponse(
                content={"status": "not ready", "services": _health_state["services"]},
                status_code=503
            )

    @app.get("/live")
    async def liveness():
        """Liveness check endpoint (always returns 200)"""
        return {"status": "alive"}

else:
    app = None


# Monitoring helpers
class MetricsContext:
    """Context manager for tracking metrics"""

    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        increment_tasks()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        decrement_tasks()

        # Record metrics
        if exc_type is None:
            # Success
            if "agent_type" in self.labels:
                tasks_total.labels(**self.labels, status="success").inc()
                task_duration.labels(agent_type=self.labels["agent_type"]).observe(duration)
        else:
            # Error
            increment_errors()
            if "agent_type" in self.labels:
                tasks_total.labels(**self.labels, status="error").inc()
            errors_total.labels(error_type=exc_type.__name__).inc()

        return False  # Don't suppress exceptions


def track_task(agent_type: str):
    """Decorator for tracking task metrics"""
    return MetricsContext("task", {"agent_type": agent_type})


def track_checkpoint(operation: str):
    """Track checkpoint operation"""
    checkpoint_operations.labels(operation=operation).inc()


def track_checkpoint_duration(operation: str, duration: float):
    """Track checkpoint operation duration"""
    checkpoint_duration.labels(operation=operation).observe(duration)


def track_workflow(status: str, node_count: int):
    """Track workflow execution"""
    workflow_executions.labels(status=status).inc()
    workflow_nodes.observe(node_count)


# Main function to run health API
async def run_health_api(host: str = "0.0.0.0", port: int = 8000):
    """Run health check API server"""
    if not HAS_FASTAPI:
        print("FastAPI not installed. Health API not available.")
        return

    import uvicorn

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if HAS_FASTAPI:
        asyncio.run(run_health_api())
    else:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn")
