"""
Domain Model & Manager for Alert Service (F3-K2-A / F3-K2-C).
Handles Alert Deduplication, Cooldown Logic, Reopen Triggers, and Evidence Immutability.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import copy


class ImmutableEvidenceError(Exception):
    """Raised when an attempt is made to mutate a frozen/immutable evidence snapshot."""
    pass


class AlertStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    SUPPRESSED = "SUPPRESSED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertModel:
    def __init__(
        self,
        target_address: str,
        rule_code: str,
        severity: SeverityEnum,
        evidence_snapshot: List[Dict[str, Any]],
        correlation_id: Optional[str] = None,
        cooldown_seconds: int = 300,
        now: Optional[datetime] = None,
    ):
        self.alert_id: str = f"alt-{uuid.uuid4().hex[:12]}"
        self.target_address: str = target_address
        self.rule_code: str = rule_code
        self.severity: SeverityEnum = severity
        self.status: AlertStatus = AlertStatus.NEW
        self.occurrence_count: int = 1
        
        current_time = now or datetime.now(timezone.utc)
        self.first_seen_at: datetime = current_time
        self.last_seen_at: datetime = current_time
        self.cooldown_until: datetime = current_time + timedelta(seconds=cooldown_seconds)
        
        # Deepcopy & freeze evidence snapshot to guarantee immutability
        self._evidence_snapshot: List[Dict[str, Any]] = copy.deepcopy(evidence_snapshot)
        self.correlation_ids: List[str] = [correlation_id] if correlation_id else []

    @property
    def evidence_snapshot(self) -> List[Dict[str, Any]]:
        """Returns a deep copy of the evidence snapshot to prevent external mutation."""
        return copy.deepcopy(self._evidence_snapshot)

    def mutate_evidence_attempt(self, index: int, new_data: Dict[str, Any]):
        """Explicit method attempting mutation to verify immutability guard."""
        raise ImmutableEvidenceError(
            f"Alert {self.alert_id} evidence snapshot is immutable and cannot be modified."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "target_address": self.target_address,
            "rule_code": self.rule_code,
            "severity": self.severity.value,
            "status": self.status.value,
            "occurrence_count": self.occurrence_count,
            "first_seen_at": self.first_seen_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "cooldown_until": self.cooldown_until.isoformat(),
            "evidence_snapshot": self.evidence_snapshot,
            "correlation_ids": self.correlation_ids,
        }


class AlertManager:
    """In-Memory Alert Management Engine for Deduplication, Cooldown, and Reopen logic."""
    def __init__(self, default_cooldown_seconds: int = 300):
        self.default_cooldown_seconds = default_cooldown_seconds
        # Storage keyed by (target_address, rule_code)
        self._alerts: Dict[str, AlertModel] = {}
        self._alert_history: List[AlertModel] = []

    def _make_key(self, target_address: str, rule_code: str) -> str:
        return f"{target_address.lower()}:{rule_code}"

    def process_risk_signal(
        self,
        target_address: str,
        rule_code: str,
        severity: SeverityEnum,
        evidence: List[Dict[str, Any]],
        correlation_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> AlertModel:
        """
        Processes an incoming risk signal and deterministically handles:
        1. Deduplication & Cooldown suppression if within cooldown window.
        2. Reopen trigger if previously closed and cooldown has elapsed.
        3. New Alert creation if no existing alert.
        """
        current_time = now or datetime.now(timezone.utc)
        key = self._make_key(target_address, rule_code)
        existing_alert = self._alerts.get(key)

        if existing_alert:
            # Case A: Within Cooldown Window -> Deduplicate & Suppress
            if current_time <= existing_alert.cooldown_until:
                existing_alert.occurrence_count += 1
                existing_alert.last_seen_at = current_time
                if correlation_id and correlation_id not in existing_alert.correlation_ids:
                    existing_alert.correlation_ids.append(correlation_id)
                if existing_alert.status != AlertStatus.CLOSED:
                    existing_alert.status = AlertStatus.SUPPRESSED
                return existing_alert

            # Case B: Cooldown Elapsed & Alert was CLOSED -> Reopen
            if existing_alert.status == AlertStatus.CLOSED:
                existing_alert.status = AlertStatus.REOPENED
                existing_alert.occurrence_count += 1
                existing_alert.last_seen_at = current_time
                existing_alert.cooldown_until = current_time + timedelta(seconds=self.default_cooldown_seconds)
                if correlation_id and correlation_id not in existing_alert.correlation_ids:
                    existing_alert.correlation_ids.append(correlation_id)
                return existing_alert

            # Case C: Cooldown Elapsed & Alert was Active/Suppressed -> Reactivate
            existing_alert.status = AlertStatus.ACTIVE
            existing_alert.occurrence_count += 1
            existing_alert.last_seen_at = current_time
            existing_alert.cooldown_until = current_time + timedelta(seconds=self.default_cooldown_seconds)
            if correlation_id and correlation_id not in existing_alert.correlation_ids:
                existing_alert.correlation_ids.append(correlation_id)
            return existing_alert

        # Case D: New Alert
        new_alert = AlertModel(
            target_address=target_address,
            rule_code=rule_code,
            severity=severity,
            evidence_snapshot=evidence,
            correlation_id=correlation_id,
            cooldown_seconds=self.default_cooldown_seconds,
            now=current_time,
        )
        self._alerts[key] = new_alert
        self._alert_history.append(new_alert)
        return new_alert

    def close_alert(self, target_address: str, rule_code: str) -> Optional[AlertModel]:
        key = self._make_key(target_address, rule_code)
        alert = self._alerts.get(key)
        if alert:
            alert.status = AlertStatus.CLOSED
        return alert

    def get_alert(self, target_address: str, rule_code: str) -> Optional[AlertModel]:
        key = self._make_key(target_address, rule_code)
        return self._alerts.get(key)
