import json
import logging
import sys
import unittest
from io import StringIO
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "packages" / "observability" / "python"
sys.path.insert(0, str(PACKAGE_ROOT))

from cryptoaml_observability.context import (  # noqa: E402
    TraceContext,
    context_scope,
    parse_traceparent,
    resolve_trace_context,
)
from cryptoaml_observability.health import HealthRegistry, HealthStatus  # noqa: E402
from cryptoaml_observability.logging import configure_logging, get_logger  # noqa: E402
from cryptoaml_observability.telemetry import TelemetryConfig, configure_telemetry  # noqa: E402


class ObservabilityTests(unittest.TestCase):
    def test_traceparent_is_parsed_and_child_keeps_trace_id(self):
        context = parse_traceparent("00-" + "a" * 32 + "-" + "b" * 16 + "-01")
        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.trace_id, "a" * 32)
        self.assertEqual(context.child().trace_id, context.trace_id)
        self.assertNotEqual(context.child().span_id, context.span_id)

    def test_invalid_traceparent_creates_new_context(self):
        context = resolve_trace_context({"TraceParent": "not-valid"})
        self.assertEqual(len(context.trace_id), 32)
        self.assertEqual(len(context.span_id), 16)

    def test_json_log_contains_context_and_extra_fields(self):
        stream = StringIO()
        configure_logging(stream=stream)
        logger = get_logger("test")
        with context_scope(TraceContext.new()):
            logger.info("fixture loaded", extra={"event": "fixture.loaded"})
        payload = json.loads(stream.getvalue().strip().splitlines()[-1])
        self.assertEqual(payload["event"], "fixture.loaded")
        self.assertIn("trace_id", payload)
        self.assertIn("correlation_id", payload)

    def test_readiness_fails_when_dependency_fails(self):
        registry = HealthRegistry("test-service")
        registry.register("postgres", lambda: True)
        registry.register("neo4j", lambda: False)
        report = registry.readiness()
        self.assertEqual(report.status, HealthStatus.FAIL)
        self.assertEqual(report.http_status, 503)

    def test_liveness_and_startup_are_separate(self):
        registry = HealthRegistry("test-service")
        self.assertEqual(registry.liveness().status, HealthStatus.OK)
        self.assertEqual(registry.startup(False).status, HealthStatus.FAIL)

    def test_telemetry_bootstraps_without_sdk(self):
        telemetry = configure_telemetry(TelemetryConfig("test-service"))
        with telemetry.span("fixture.load"):
            pass


if __name__ == "__main__":
    unittest.main()
