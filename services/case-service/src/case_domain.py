"""
Domain Model & Manager for Case Management Service (F3-K2-B / F3-K2-C).
Handles Case Lifecycle, SLA Deadlines, Reopen Scenarios, Analyst Dispositions, and Immutable Evidence.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import copy


class ImmutableEvidenceError(Exception):
    """Raised when evidence snapshot tampering or mutation is attempted."""
    pass


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class DispositionType(str, Enum):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    BENIGN_SUSPICION = "BENIGN_SUSPICION"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseDispositionEvent:
    def __init__(
        self,
        case_id: str,
        analyst_id: str,
        disposition: DispositionType,
        notes: str = "",
        now: Optional[datetime] = None,
    ):
        self.disposition_id: str = f"dsp-{uuid.uuid4().hex[:12]}"
        self.case_id: str = case_id
        self.analyst_id: str = analyst_id
        self.disposition: DispositionType = disposition
        self.notes: str = notes
        self.created_at: datetime = now or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disposition_id": self.disposition_id,
            "case_id": self.case_id,
            "analyst_id": self.analyst_id,
            "disposition": self.disposition.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class CaseModel:
    SLA_HOURS_MAP: Dict[SeverityEnum, int] = {
        SeverityEnum.CRITICAL: 2,
        SeverityEnum.HIGH: 12,
        SeverityEnum.MEDIUM: 24,
        SeverityEnum.LOW: 48,
    }

    def __init__(
        self,
        target_address: str,
        severity: SeverityEnum,
        alert_id: str,
        evidence_snapshot: List[Dict[str, Any]],
        now: Optional[datetime] = None,
    ):
        self.case_id: str = f"cas-{uuid.uuid4().hex[:12]}"
        self.target_address: str = target_address
        self.severity: SeverityEnum = severity
        self.status: CaseStatus = CaseStatus.OPEN
        self.alert_ids: List[str] = [alert_id]
        
        current_time = now or datetime.now(timezone.utc)
        self.created_at: datetime = current_time
        self.updated_at: datetime = current_time
        
        # Calculate SLA Due Time deterministically
        sla_hours = self.SLA_HOURS_MAP.get(severity, 24)
        self.sla_due_at: datetime = current_time + timedelta(hours=sla_hours)
        
        # Immutable evidence snapshot
        self._evidence_snapshot: List[Dict[str, Any]] = copy.deepcopy(evidence_snapshot)
        self.dispositions: List[CaseDispositionEvent] = []

    @property
    def evidence_snapshot(self) -> List[Dict[str, Any]]:
        """Returns a deep copy of evidence to guarantee immutability."""
        return copy.deepcopy(self._evidence_snapshot)

    def is_sla_breached(self, at_time: Optional[datetime] = None) -> bool:
        """Deterministically evaluates if Case SLA deadline has been breached."""
        check_time = at_time or datetime.now(timezone.utc)
        if self.status in [CaseStatus.CLOSED]:
            return False
        return check_time > self.sla_due_at

    def mutate_evidence_attempt(self):
        raise ImmutableEvidenceError(
            f"Case {self.case_id} evidence snapshot is immutable and protected."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "target_address": self.target_address,
            "severity": self.severity.value,
            "status": self.status.value,
            "alert_ids": self.alert_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sla_due_at": self.sla_due_at.isoformat(),
            "is_sla_breached": self.is_sla_breached(),
            "evidence_snapshot": self.evidence_snapshot,
            "dispositions": [d.to_dict() for d in self.dispositions],
        }


class CaseManager:
    """In-Memory Case Management Engine supporting Lifecycle, SLA, Reopen, and Disposition tracking."""
    def __init__(self):
        self._cases: Dict[str, CaseModel] = {}

    def get_or_create_case(
        self,
        target_address: str,
        severity: SeverityEnum,
        alert_id: str,
        evidence: List[Dict[str, Any]],
        now: Optional[datetime] = None,
    ) -> CaseModel:
        """
        Creates a new case or reopens an existing closed case for a target address.
        """
        current_time = now or datetime.now(timezone.utc)
        existing_case = self._cases.get(target_address.lower())

        if existing_case:
            if alert_id not in existing_case.alert_ids:
                existing_case.alert_ids.append(alert_id)
            existing_case.updated_at = current_time

            # Case Reopen scenario
            if existing_case.status == CaseStatus.CLOSED:
                existing_case.status = CaseStatus.REOPENED
                # Recalculate SLA on reopen
                sla_hours = CaseModel.SLA_HOURS_MAP.get(severity, 24)
                existing_case.sla_due_at = current_time + timedelta(hours=sla_hours)
                existing_case.severity = severity

            return existing_case

        new_case = CaseModel(
            target_address=target_address,
            severity=severity,
            alert_id=alert_id,
            evidence_snapshot=evidence,
            now=current_time,
        )
        self._cases[target_address.lower()] = new_case
        return new_case

    def add_disposition(
        self,
        case_id: str,
        analyst_id: str,
        disposition: DispositionType,
        notes: str = "",
        now: Optional[datetime] = None,
    ) -> CaseDispositionEvent:
        """Appends an analyst disposition event and transitions case status."""
        target_case = None
        for c in self._cases.values():
            if c.case_id == case_id:
                target_case = c
                break

        if not target_case:
            raise KeyError(f"Case {case_id} not found.")

        disp = CaseDispositionEvent(
            case_id=case_id,
            analyst_id=analyst_id,
            disposition=disposition,
            notes=notes,
            now=now,
        )
        target_case.dispositions.append(disp)
        target_case.updated_at = now or datetime.now(timezone.utc)

        # Transition status based on disposition
        if disposition in [DispositionType.TRUE_POSITIVE, DispositionType.FALSE_POSITIVE]:
            target_case.status = CaseStatus.CLOSED
        elif disposition == DispositionType.NEEDS_MORE_INFO:
            target_case.status = CaseStatus.IN_REVIEW

        return disp

    def get_case(self, case_id: str) -> Optional[CaseModel]:
        for c in self._cases.values():
            if c.case_id == case_id:
                return c
        return None
