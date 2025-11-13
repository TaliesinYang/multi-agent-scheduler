"""
Distributed Tracing System

Lightweight tracing for multi-agent workflows.
Compatible with OpenTelemetry concepts.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from contextlib import asynccontextmanager
import asyncio


class SpanKind(Enum):
    """Span kinds"""
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Span status"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """Trace span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })

    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.attributes[key] = value

    def set_status(self, status: SpanStatus, description: Optional[str] = None):
        """Set span status"""
        self.status = status
        if description:
            self.attributes["status_description"] = description

    def end(self):
        """End span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events
        }


class Tracer:
    """Lightweight tracer"""

    def __init__(self, service_name: str = "multi-agent-scheduler"):
        self.service_name = service_name
        self.current_trace_id: Optional[str] = None
        self.current_span: Optional[Span] = None
        self.spans: List[Span] = []

    def start_trace(self) -> str:
        """Start new trace"""
        self.current_trace_id = str(uuid.uuid4())
        return self.current_trace_id

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start new span"""
        if not self.current_trace_id:
            self.start_trace()

        span = Span(
            trace_id=self.current_trace_id,
            span_id=str(uuid.uuid4())[:16],
            parent_span_id=self.current_span.span_id if self.current_span else None,
            name=name,
            kind=kind,
            start_time=time.time(),
            attributes=attributes or {}
        )

        # Add service name
        span.set_attribute("service.name", self.service_name)

        self.current_span = span
        return span

    def end_span(self, span: Span):
        """End span"""
        span.end()
        self.spans.append(span)

    @asynccontextmanager
    async def trace(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing"""
        span = self.start_span(name, kind, attributes)
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            span.set_attribute("exception.type", type(e).__name__)
            span.set_attribute("exception.message", str(e))
            raise
        finally:
            self.end_span(span)

    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for trace"""
        return [s for s in self.spans if s.trace_id == trace_id]

    def get_trace_tree(self, trace_id: str) -> Dict[str, Any]:
        """Get trace as tree structure"""
        spans = self.get_trace(trace_id)
        if not spans:
            return {}

        # Build tree
        root_spans = [s for s in spans if s.parent_span_id is None]
        if not root_spans:
            return {}

        def build_tree(span: Span) -> Dict[str, Any]:
            children = [s for s in spans if s.parent_span_id == span.span_id]
            return {
                **span.to_dict(),
                "children": [build_tree(child) for child in children]
            }

        return build_tree(root_spans[0])


class TracingExporter:
    """Export traces to various backends"""

    def __init__(self, tracer: Tracer):
        self.tracer = tracer

    def export_to_console(self, trace_id: str):
        """Print trace to console"""
        tree = self.tracer.get_trace_tree(trace_id)
        self._print_tree(tree, indent=0)

    def _print_tree(self, node: Dict[str, Any], indent: int = 0):
        """Print trace tree"""
        prefix = "  " * indent
        name = node.get("name", "unknown")
        duration = node.get("duration_ms", 0)
        status = node.get("status", "unset")

        print(f"{prefix}├─ {name} ({duration:.2f}ms) [{status}]")

        for child in node.get("children", []):
            self._print_tree(child, indent + 1)

    def export_to_json(self, trace_id: str) -> str:
        """Export trace as JSON"""
        import json
        tree = self.tracer.get_trace_tree(trace_id)
        return json.dumps(tree, indent=2)


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "multi-agent-scheduler") -> Tracer:
    """Get global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer


# Integration helpers
async def trace_agent_call(agent_name: str, prompt: str, call_func):
    """Trace an agent call"""
    tracer = get_tracer()
    async with tracer.trace(f"agent.{agent_name}.call", SpanKind.CLIENT) as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("prompt.length", len(prompt))
        span.set_attribute("prompt.preview", prompt[:100])

        result = await call_func()

        span.set_attribute("result.success", result.get("success", False))
        span.set_attribute("result.tokens", result.get("tokens", 0))

        return result


async def trace_workflow_execution(workflow_id: str, execute_func):
    """Trace workflow execution"""
    tracer = get_tracer()
    async with tracer.trace(f"workflow.{workflow_id}", SpanKind.INTERNAL) as span:
        span.set_attribute("workflow.id", workflow_id)

        result = await execute_func()

        span.set_attribute("workflow.node_count", len(result.history))
        span.set_attribute("workflow.duration", result.metadata.get("duration", 0))

        return result


async def trace_task_execution(task_id: str, execute_func):
    """Trace task execution"""
    tracer = get_tracer()
    async with tracer.trace(f"task.{task_id}", SpanKind.INTERNAL) as span:
        span.set_attribute("task.id", task_id)

        result = await execute_func()

        span.set_attribute("task.success", result.get("success", False))
        span.set_attribute("task.latency", result.get("latency", 0))

        return result
