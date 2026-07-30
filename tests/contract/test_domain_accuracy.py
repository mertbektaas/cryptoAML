"""
Domain Accuracy & Contract Test Suite for F3-K2-C.
Verifies Alert Deduplication, Cooldown, Reopen, Evidence Immutability, Case SLA, and Disposition Determinism.
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime, timezone, timedelta

# Add service paths to sys.path to allow imports
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "services" / "alert-service" / "src"))
sys.path.insert(0, str(repo_root / "services" / "case-service" / "src"))

from alert_domain import (
    AlertManager,
    AlertStatus,
    SeverityEnum as AlertSeverityEnum,
    ImmutableEvidenceError as AlertImmutableEvidenceError,
)
from case_domain import (
    CaseManager,
    CaseStatus,
    DispositionType,
    SeverityEnum as CaseSeverityEnum,
    ImmutableEvidenceError as CaseImmutableEvidenceError,
)


@pytest.fixture
def sample_evidence():
    return [
        {
            "source_type": "ON_CHAIN_TX",
            "reference_uri": "eip155:1/tx/0x123abc456def",
            "observed_at": "2026-07-30T09:00:00Z",
            "raw_payload_snippet": {"amount_wei": 1000000000000000000},
        },
        {
            "source_type": "SANCTION_LIST",
            "reference_uri": "ofac://sanction-list/eth-0xbad123",
            "observed_at": "2026-07-30T09:00:00Z",
        },
    ]


def test_alert_deduplication_and_cooldown_suppression(sample_evidence):
    """Verifies that signals received within cooldown (300s) are suppressed & deduplicated."""
    alert_mgr = AlertManager(default_cooldown_seconds=300)
    target = "0x1111222233334444555566667777888899990000"
    rule = "HIGH_RISK_LABEL_EXPOSURE"
    t0 = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)

    # First Signal -> Creates NEW Alert
    alert1 = alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.CRITICAL,
        evidence=sample_evidence,
        correlation_id="corr-1",
        now=t0,
    )
    assert alert1.status == AlertStatus.NEW
    assert alert1.occurrence_count == 1
    assert len(alert1.correlation_ids) == 1

    # Second Signal after 100s (Within 300s cooldown) -> Deduplicated & Suppressed
    t1 = t0 + timedelta(seconds=100)
    alert2 = alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.CRITICAL,
        evidence=sample_evidence,
        correlation_id="corr-2",
        now=t1,
    )
    assert alert2.alert_id == alert1.alert_id
    assert alert2.status == AlertStatus.SUPPRESSED
    assert alert2.occurrence_count == 2
    assert "corr-2" in alert2.correlation_ids


def test_alert_cooldown_elapsed_reactivation(sample_evidence):
    """Verifies that after cooldown elapses (>300s), a new signal reactivates the alert."""
    alert_mgr = AlertManager(default_cooldown_seconds=300)
    target = "0x2222333344445555666677778888999900001111"
    rule = "RAPID_PASS_THROUGH"
    t0 = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)

    alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.HIGH,
        evidence=sample_evidence,
        now=t0,
    )

    # Signal after 350s (> 300s cooldown) -> Reactivates Alert
    t1 = t0 + timedelta(seconds=350)
    alert2 = alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.HIGH,
        evidence=sample_evidence,
        now=t1,
    )
    assert alert2.status == AlertStatus.ACTIVE
    assert alert2.occurrence_count == 2


def test_alert_reopen_scenario(sample_evidence):
    """Verifies that a closed alert is set to REOPENED when a new signal arrives post-cooldown."""
    alert_mgr = AlertManager(default_cooldown_seconds=300)
    target = "0x3333444455556666777788889999000011112222"
    rule = "FAN_IN_STRUCTURING"
    t0 = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)

    alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.HIGH,
        evidence=sample_evidence,
        now=t0,
    )

    # Close the alert
    alert_mgr.close_alert(target, rule)
    closed_alert = alert_mgr.get_alert(target, rule)
    assert closed_alert.status == AlertStatus.CLOSED

    # Signal after 400s -> Triggers REOPENED
    t1 = t0 + timedelta(seconds=400)
    reopened_alert = alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.HIGH,
        evidence=sample_evidence,
        now=t1,
    )
    assert reopened_alert.status == AlertStatus.REOPENED
    assert reopened_alert.occurrence_count == 2


def test_evidence_snapshot_immutability(sample_evidence):
    """Verifies that evidence snapshots are frozen and immutable against external tampering."""
    alert_mgr = AlertManager()
    target = "0x4444555566667777888899990000111122223333"
    rule = "TEST_RULE"

    alert = alert_mgr.process_risk_signal(
        target_address=target,
        rule_code=rule,
        severity=AlertSeverityEnum.MEDIUM,
        evidence=sample_evidence,
    )

    # Attempt to mutate returned evidence property
    retrieved_evidence = alert.evidence_snapshot
    retrieved_evidence[0]["reference_uri"] = "MUTATED_TAMPERED_URI"

    # Original evidence inside alert object must remain unchanged!
    assert alert.evidence_snapshot[0]["reference_uri"] == "eip155:1/tx/0x123abc456def"

    # Explicit mutation method must raise ImmutableEvidenceError
    with pytest.raises(AlertImmutableEvidenceError):
        alert.mutate_evidence_attempt(0, {"reference_uri": "BAD"})


def test_case_sla_calculation_and_breach(sample_evidence):
    """Verifies SLA deadline calculation per severity and deterministic breach evaluation."""
    case_mgr = CaseManager()
    target = "0x5555666677778888999900001111222233334444"
    t0 = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)

    # CRITICAL Severity Case -> SLA = 2 Hours
    critical_case = case_mgr.get_or_create_case(
        target_address=target,
        severity=CaseSeverityEnum.CRITICAL,
        alert_id="alt-1",
        evidence=sample_evidence,
        now=t0,
    )
    assert critical_case.sla_due_at == t0 + timedelta(hours=2)

    # Check SLA before 2h -> Not Breached
    t_before = t0 + timedelta(hours=1)
    assert critical_case.is_sla_breached(at_time=t_before) is False

    # Check SLA after 2h 1m -> Breached!
    t_after = t0 + timedelta(hours=2, minutes=1)
    assert critical_case.is_sla_breached(at_time=t_after) is True


def test_case_reopen_and_disposition_events(sample_evidence):
    """Verifies Case creation, analyst disposition event logging, closing, and reopening."""
    case_mgr = CaseManager()
    target = "0x6666777788889999000011112222333344445555"
    t0 = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)

    # Create Case
    case = case_mgr.get_or_create_case(
        target_address=target,
        severity=CaseSeverityEnum.HIGH,
        alert_id="alt-100",
        evidence=sample_evidence,
        now=t0,
    )
    assert case.status == CaseStatus.OPEN

    # Add Disposition -> TRUE_POSITIVE -> Closes Case
    disp = case_mgr.add_disposition(
        case_id=case.case_id,
        analyst_id="analyst-007",
        disposition=DispositionType.TRUE_POSITIVE,
        notes="Confirmed OFAC sanctioned address interaction.",
        now=t0 + timedelta(minutes=30),
    )
    assert disp.analyst_id == "analyst-007"
    assert case.status == CaseStatus.CLOSED

    # Subsequent alert for same target -> Case REOPENED
    reopened_case = case_mgr.get_or_create_case(
        target_address=target,
        severity=CaseSeverityEnum.CRITICAL,
        alert_id="alt-101",
        evidence=sample_evidence,
        now=t0 + timedelta(hours=5),
    )
    assert reopened_case.status == CaseStatus.REOPENED
    assert "alt-101" in reopened_case.alert_ids


def test_deterministic_end_to_end_replay(sample_evidence):
    """Runs 50 sequential replays of risk signals to assert 100% deterministic output consistency."""
    results = []
    t0 = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)

    for run_idx in range(50):
        alert_mgr = AlertManager(default_cooldown_seconds=300)
        case_mgr = CaseManager()

        a1 = alert_mgr.process_risk_signal(
            target_address="0x7777888899990000111122223333444455556666",
            rule_code="TEST_DETERMINISM",
            severity=AlertSeverityEnum.HIGH,
            evidence=sample_evidence,
            correlation_id="corr-det",
            now=t0,
        )
        c1 = case_mgr.get_or_create_case(
            target_address="0x7777888899990000111122223333444455556666",
            severity=CaseSeverityEnum.HIGH,
            alert_id=a1.alert_id,
            evidence=sample_evidence,
            now=t0,
        )

        results.append((a1.status, a1.occurrence_count, c1.status, c1.sla_due_at.isoformat()))

    # Assert that all 50 test runs yielded identical results
    first_result = results[0]
    for idx, r in enumerate(results):
        assert r == first_result, f"Non-deterministic variance found at run {idx}: {r} != {first_result}"
