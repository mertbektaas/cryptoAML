"""Framework-neutral health/readiness contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from time import monotonic
from collections.abc import Callable, Mapping


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class HealthResult:
    name: str
    status: HealthStatus
    detail: str | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"status": self.status.value}
        if self.detail:
            result["detail"] = self.detail
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 3)
        return result


@dataclass(frozen=True, slots=True)
class HealthReport:
    component: str
    status: HealthStatus
    checks: Mapping[str, HealthResult] = field(default_factory=dict)

    @property
    def http_status(self) -> int:
        return 200 if self.status is HealthStatus.OK else 503

    def to_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "status": self.status.value,
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
        }


HealthCheck = Callable[[], bool | HealthResult]


class HealthRegistry:
    """Run dependency checks for a readiness response."""

    def __init__(self, component: str):
        self.component = component
        self._checks: dict[str, HealthCheck] = {}

    def register(self, name: str, check: HealthCheck) -> None:
        if not name or name in self._checks:
            raise ValueError("health check names must be non-empty and unique")
        self._checks[name] = check

    def liveness(self) -> HealthReport:
        return HealthReport(self.component, HealthStatus.OK)

    def startup(self, started: bool) -> HealthReport:
        status = HealthStatus.OK if started else HealthStatus.FAIL
        return HealthReport(self.component, status)

    def readiness(self) -> HealthReport:
        results: dict[str, HealthResult] = {}
        for name, check in self._checks.items():
            started = monotonic()
            try:
                outcome = check()
                if isinstance(outcome, HealthResult):
                    result = outcome
                else:
                    result = HealthResult(name, HealthStatus.OK if outcome else HealthStatus.FAIL)
            except Exception as error:  # readiness must never crash the process
                result = HealthResult(name, HealthStatus.FAIL, detail=str(error))
            if result.latency_ms is None:
                result = HealthResult(
                    result.name,
                    result.status,
                    result.detail,
                    (monotonic() - started) * 1000,
                )
            results[name] = result
        overall = HealthStatus.OK if all(item.status is HealthStatus.OK for item in results.values()) else HealthStatus.FAIL
        return HealthReport(self.component, overall, results)
