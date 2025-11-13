"""
Comprehensive tests for distributed tracing system
"""
import pytest
import asyncio
import time
from typing import Dict, Any, List, Optional
from src.tracing import (
    SpanKind, SpanStatus, Span, Tracer, TracingExporter,
    get_tracer, set_global_tracer
)


class TestSpan:
    """Test Span class"""

    def test_create_span(self):
        """Test creating a span"""
        span = Span(
            trace_id="trace_123",
            span_id="span_456",
            parent_span_id=None,
            name="test_operation",
            kind=SpanKind.INTERNAL,
            start_time=time.time()
        )

        assert span.trace_id == "trace_123"
        assert span.span_id == "span_456"
        assert span.parent_span_id is None
        assert span.name == "test_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.status == SpanStatus.UNSET

    def test_set_attribute(self):
        """Test setting span attributes"""
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="operation",
            kind=SpanKind.INTERNAL,
            start_time=time.time()
        )

        span.set_attribute("user_id", "user_123")
        span.set_attribute("request_count", 42)

        assert span.attributes["user_id"] == "user_123"
        assert span.attributes["request_count"] == 42

    def test_add_event(self):
        """Test adding events to span"""
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="operation",
            kind=SpanKind.INTERNAL,
            start_time=time.time()
        )

        span.add_event("cache_miss", {"key": "user_data"})
        span.add_event("database_query", {"query": "SELECT * FROM users"})

        assert len(span.events) == 2
        assert span.events[0]["name"] == "cache_miss"
        assert span.events[1]["attributes"]["query"] == "SELECT * FROM users"

    def test_set_status(self):
        """Test setting span status"""
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="operation",
            kind=SpanKind.INTERNAL,
            start_time=time.time()
        )

        span.set_status(SpanStatus.OK, "Success")
        assert span.status == SpanStatus.OK
        assert span.status_message == "Success"

        span.set_status(SpanStatus.ERROR, "Failed")
        assert span.status == SpanStatus.ERROR
        assert span.status_message == "Failed"

    def test_end_span(self):
        """Test ending a span"""
        start = time.time()
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="operation",
            kind=SpanKind.INTERNAL,
            start_time=start
        )

        time.sleep(0.01)  # Small delay
        span.end()

        assert span.end_time is not None
        assert span.end_time > start
        assert span.duration() > 0

    def test_duration(self):
        """Test calculating span duration"""
        start = time.time()
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="operation",
            kind=SpanKind.INTERNAL,
            start_time=start
        )

        # Before ending
        assert span.duration() is None

        # After ending
        time.sleep(0.01)
        end = time.time()
        span.end_time = end

        duration = span.duration()
        assert duration is not None
        assert duration > 0

    def test_to_dict(self):
        """Test span serialization"""
        span = Span(
            trace_id="trace_1",
            span_id="span_1",
            parent_span_id=None,
            name="test_op",
            kind=SpanKind.CLIENT,
            start_time=123456.789
        )
        span.set_attribute("key", "value")
        span.add_event("event1", {})
        span.end()

        span_dict = span.to_dict()

        assert span_dict["trace_id"] == "trace_1"
        assert span_dict["span_id"] == "span_1"
        assert span_dict["name"] == "test_op"
        assert span_dict["kind"] == "client"
        assert "key" in span_dict["attributes"]
        assert len(span_dict["events"]) == 1


class TestTracer:
    """Test Tracer class"""

    def test_create_tracer(self):
        """Test creating a tracer"""
        tracer = Tracer(service_name="test_service")

        assert tracer.service_name == "test_service"
        assert tracer.current_trace_id is None

    def test_start_span(self):
        """Test starting a span"""
        tracer = Tracer(service_name="test_service")

        span = tracer.start_span("operation_1", SpanKind.INTERNAL)

        assert span is not None
        assert span.name == "operation_1"
        assert span.kind == SpanKind.INTERNAL
        assert span.trace_id is not None
        assert span.span_id is not None

    def test_end_span(self):
        """Test ending a span"""
        tracer = Tracer(service_name="test_service")

        span = tracer.start_span("operation")
        assert span.end_time is None

        tracer.end_span(span)

        assert span.end_time is not None
        assert span in tracer.completed_spans

    def test_nested_spans(self):
        """Test creating nested spans"""
        tracer = Tracer(service_name="test_service")

        parent_span = tracer.start_span("parent", SpanKind.INTERNAL)
        child_span = tracer.start_span("child", SpanKind.INTERNAL)

        assert child_span.parent_span_id == parent_span.span_id
        assert child_span.trace_id == parent_span.trace_id

        tracer.end_span(child_span)
        tracer.end_span(parent_span)

    @pytest.mark.asyncio
    async def test_trace_context_manager(self):
        """Test trace context manager"""
        tracer = Tracer(service_name="test_service")

        async with tracer.trace("my_operation", SpanKind.INTERNAL) as span:
            span.set_attribute("test", "value")
            await asyncio.sleep(0.01)

        # Span should be ended and recorded
        assert span.end_time is not None
        assert span.status == SpanStatus.OK
        assert span in tracer.completed_spans

    @pytest.mark.asyncio
    async def test_trace_with_error(self):
        """Test trace context manager with error"""
        tracer = Tracer(service_name="test_service")

        with pytest.raises(ValueError):
            async with tracer.trace("failing_op") as span:
                raise ValueError("Test error")

        # Should have recorded the span with error status
        completed = tracer.get_completed_spans()
        assert len(completed) == 1
        assert completed[0].status == SpanStatus.ERROR
        assert "Test error" in completed[0].status_message

    @pytest.mark.asyncio
    async def test_nested_trace_contexts(self):
        """Test nested trace context managers"""
        tracer = Tracer(service_name="test_service")

        async with tracer.trace("parent_op") as parent:
            parent.set_attribute("level", "parent")

            async with tracer.trace("child_op") as child:
                child.set_attribute("level", "child")
                assert child.parent_span_id == parent.span_id

        completed = tracer.get_completed_spans()
        assert len(completed) == 2

    def test_get_current_span(self):
        """Test getting current active span"""
        tracer = Tracer(service_name="test_service")

        assert tracer.get_current_span() is None

        span = tracer.start_span("operation")
        assert tracer.get_current_span() == span

        tracer.end_span(span)
        assert tracer.get_current_span() is None

    def test_get_completed_spans(self):
        """Test getting completed spans"""
        tracer = Tracer(service_name="test_service")

        span1 = tracer.start_span("op1")
        tracer.end_span(span1)

        span2 = tracer.start_span("op2")
        tracer.end_span(span2)

        completed = tracer.get_completed_spans()
        assert len(completed) == 2

    def test_clear_spans(self):
        """Test clearing completed spans"""
        tracer = Tracer(service_name="test_service")

        span = tracer.start_span("op")
        tracer.end_span(span)

        assert len(tracer.completed_spans) == 1

        tracer.clear_spans()

        assert len(tracer.completed_spans) == 0

    def test_get_trace_by_id(self):
        """Test getting all spans for a trace"""
        tracer = Tracer(service_name="test_service")

        parent = tracer.start_span("parent")
        child1 = tracer.start_span("child1")
        tracer.end_span(child1)
        child2 = tracer.start_span("child2")
        tracer.end_span(child2)
        tracer.end_span(parent)

        trace_id = parent.trace_id
        trace_spans = tracer.get_trace_by_id(trace_id)

        assert len(trace_spans) == 3
        assert all(s.trace_id == trace_id for s in trace_spans)


class TestTracingExporter:
    """Test TracingExporter class"""

    def test_create_exporter(self):
        """Test creating an exporter"""
        exporter = TracingExporter()

        assert exporter.export_count == 0

    @pytest.mark.asyncio
    async def test_export_spans(self):
        """Test exporting spans"""
        exporter = TracingExporter()
        tracer = Tracer(service_name="test_service")

        span1 = tracer.start_span("op1")
        tracer.end_span(span1)

        span2 = tracer.start_span("op2")
        tracer.end_span(span2)

        spans = tracer.get_completed_spans()
        await exporter.export(spans)

        assert exporter.export_count == 1
        assert len(exporter.exported_spans) == 2

    @pytest.mark.asyncio
    async def test_export_to_json(self):
        """Test exporting spans to JSON"""
        import json
        import tempfile

        exporter = TracingExporter()
        tracer = Tracer(service_name="test_service")

        span = tracer.start_span("operation")
        span.set_attribute("key", "value")
        tracer.end_span(span)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        await exporter.export_to_json(tracer.get_completed_spans(), filepath)

        # Verify file contents
        with open(filepath, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["name"] == "operation"
        assert data[0]["attributes"]["key"] == "value"

        # Cleanup
        import os
        os.unlink(filepath)

    def test_get_export_stats(self):
        """Test getting export statistics"""
        exporter = TracingExporter()

        stats = exporter.get_export_stats()
        assert stats["total_exports"] == 0
        assert stats["total_spans_exported"] == 0


class TestGlobalTracer:
    """Test global tracer functions"""

    def test_get_tracer(self):
        """Test getting global tracer"""
        tracer1 = get_tracer("service_1")
        tracer2 = get_tracer("service_1")

        # Should return same instance
        assert tracer1 is tracer2

    def test_different_services(self):
        """Test getting tracers for different services"""
        tracer1 = get_tracer("service_1")
        tracer2 = get_tracer("service_2")

        # Should be different instances
        assert tracer1 is not tracer2
        assert tracer1.service_name == "service_1"
        assert tracer2.service_name == "service_2"

    def test_set_global_tracer(self):
        """Test setting custom global tracer"""
        custom_tracer = Tracer(service_name="custom")
        set_global_tracer("my_service", custom_tracer)

        retrieved = get_tracer("my_service")
        assert retrieved is custom_tracer


class TestSpanKinds:
    """Test different span kinds"""

    def test_internal_span(self):
        """Test INTERNAL span kind"""
        tracer = Tracer(service_name="test")
        span = tracer.start_span("internal_op", SpanKind.INTERNAL)

        assert span.kind == SpanKind.INTERNAL

    def test_server_span(self):
        """Test SERVER span kind"""
        tracer = Tracer(service_name="test")
        span = tracer.start_span("handle_request", SpanKind.SERVER)

        assert span.kind == SpanKind.SERVER

    def test_client_span(self):
        """Test CLIENT span kind"""
        tracer = Tracer(service_name="test")
        span = tracer.start_span("api_call", SpanKind.CLIENT)

        assert span.kind == SpanKind.CLIENT

    def test_producer_span(self):
        """Test PRODUCER span kind"""
        tracer = Tracer(service_name="test")
        span = tracer.start_span("publish_message", SpanKind.PRODUCER)

        assert span.kind == SpanKind.PRODUCER

    def test_consumer_span(self):
        """Test CONSUMER span kind"""
        tracer = Tracer(service_name="test")
        span = tracer.start_span("consume_message", SpanKind.CONSUMER)

        assert span.kind == SpanKind.CONSUMER


class TestIntegration:
    """Integration tests for tracing system"""

    @pytest.mark.asyncio
    async def test_complete_trace_workflow(self):
        """Test complete tracing workflow"""
        tracer = Tracer(service_name="web_service")
        exporter = TracingExporter()

        # Simulate a web request handling multiple operations
        async with tracer.trace("handle_request", SpanKind.SERVER) as request_span:
            request_span.set_attribute("http.method", "POST")
            request_span.set_attribute("http.path", "/api/users")

            # Database query
            async with tracer.trace("db_query", SpanKind.CLIENT) as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", "SELECT * FROM users")
                await asyncio.sleep(0.01)  # Simulate query time

            # Cache lookup
            async with tracer.trace("cache_lookup", SpanKind.CLIENT) as cache_span:
                cache_span.set_attribute("cache.key", "user_123")
                cache_span.add_event("cache_miss")
                await asyncio.sleep(0.005)

            # Process data
            async with tracer.trace("process_data", SpanKind.INTERNAL) as process_span:
                process_span.set_attribute("record_count", 10)
                await asyncio.sleep(0.01)

        # Export spans
        completed = tracer.get_completed_spans()
        await exporter.export(completed)

        # Verify trace structure
        assert len(completed) == 4

        # All should have same trace_id
        trace_id = completed[0].trace_id
        assert all(s.trace_id == trace_id for s in completed)

        # Check parent-child relationships
        request_span_id = next(s.span_id for s in completed if s.name == "handle_request")
        child_spans = [s for s in completed if s.parent_span_id == request_span_id]
        assert len(child_spans) == 3

    @pytest.mark.asyncio
    async def test_distributed_trace(self):
        """Test distributed tracing across services"""
        service1_tracer = get_tracer("service_1")
        service2_tracer = get_tracer("service_2")

        # Service 1 initiates request
        async with service1_tracer.trace("initiate_request", SpanKind.CLIENT) as s1_span:
            s1_span.set_attribute("service", "service_1")
            trace_id = s1_span.trace_id

            # Service 2 receives request (same trace_id)
            service2_tracer.current_trace_id = trace_id
            async with service2_tracer.trace("handle_request", SpanKind.SERVER) as s2_span:
                s2_span.set_attribute("service", "service_2")
                assert s2_span.trace_id == trace_id

        # Verify both services traced the same distributed transaction
        s1_spans = service1_tracer.get_trace_by_id(trace_id)
        s2_spans = service2_tracer.get_trace_by_id(trace_id)

        assert len(s1_spans) == 1
        assert len(s2_spans) == 1

    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Test error tracking in traces"""
        tracer = Tracer(service_name="test_service")

        async with tracer.trace("parent_op") as parent:
            # Successful child operation
            async with tracer.trace("successful_child") as child1:
                child1.set_status(SpanStatus.OK)

            # Failing child operation
            try:
                async with tracer.trace("failing_child") as child2:
                    raise RuntimeError("Something went wrong")
            except RuntimeError:
                pass

        # Check spans
        completed = tracer.get_completed_spans()
        assert len(completed) == 3

        # Parent should be OK (didn't fail itself)
        parent_span = next(s for s in completed if s.name == "parent_op")
        assert parent_span.status == SpanStatus.OK

        # Failing child should have error status
        error_span = next(s for s in completed if s.name == "failing_child")
        assert error_span.status == SpanStatus.ERROR
        assert "Something went wrong" in error_span.status_message

    @pytest.mark.asyncio
    async def test_concurrent_traces(self):
        """Test concurrent trace operations"""
        tracer = Tracer(service_name="concurrent_service")

        async def operation(op_id: int):
            async with tracer.trace(f"operation_{op_id}") as span:
                span.set_attribute("op_id", op_id)
                await asyncio.sleep(0.01)

        # Run multiple operations concurrently
        await asyncio.gather(
            operation(1),
            operation(2),
            operation(3)
        )

        completed = tracer.get_completed_spans()
        assert len(completed) == 3

        # Each should have unique span_id
        span_ids = [s.span_id for s in completed]
        assert len(span_ids) == len(set(span_ids))

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test capturing performance metrics"""
        tracer = Tracer(service_name="perf_service")

        async with tracer.trace("slow_operation") as span:
            span.add_event("started")
            await asyncio.sleep(0.05)  # Simulate slow operation
            span.add_event("checkpoint_1")
            await asyncio.sleep(0.05)
            span.add_event("checkpoint_2")
            await asyncio.sleep(0.05)
            span.add_event("completed")

        completed = tracer.get_completed_spans()
        assert len(completed) == 1

        span = completed[0]
        assert span.duration() > 0.15  # At least 150ms
        assert len(span.events) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
