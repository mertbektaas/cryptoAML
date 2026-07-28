"""
Explainability Generator Engine for cryptoAML Platform (F2-K2-B).
Constructs transparent, auditable Evidence -> Signal -> Assessment chain explainability reports.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
try:
    from .models import (
        AssessmentEventModel,
        PolicyModel,
        SignalModel,
        RuleModel,
        EvidenceReferenceModel,
        QualityMetricsModel,
        ExplainedSignalModel,
        ReproducibilityMetadataModel,
        AssessmentExplainabilityModel
    )
except ImportError:
    from models import (
        AssessmentEventModel,
        PolicyModel,
        SignalModel,
        RuleModel,
        EvidenceReferenceModel,
        QualityMetricsModel,
        ExplainedSignalModel,
        ReproducibilityMetadataModel,
        AssessmentExplainabilityModel
    )

logger = logging.getLogger("explainability_generator")


class ExplainabilityGenerator:
    """Generates comprehensive AssessmentExplainabilityModel reports."""

    def generate_explainability(
        self,
        assessment: AssessmentEventModel,
        policy: PolicyModel,
        signals: List[SignalModel],
        git_commit_hash: str = "main-latest"
    ) -> AssessmentExplainabilityModel:
        """
        Builds a full Evidence -> Signal -> Assessment explainability model.
        """
        signal_map: Dict[str, SignalModel] = {s.id: s for s in signals}
        signal_code_map: Dict[str, SignalModel] = {s.code: s for s in signals}

        rule_map: Dict[str, RuleModel] = {}
        for r in policy.rules:
            for sig_id in r.signal_ids:
                rule_map[sig_id] = r

        explained_signals: List[ExplainedSignalModel] = []

        for matched in assessment.matched_signals:
            sig = signal_map.get(matched.signal_id) or signal_code_map.get(matched.signal_code)
            rule = rule_map.get(matched.signal_id) or rule_map.get(matched.signal_code)

            operator = rule.operator if rule else "EQUALS"
            expected_val = rule.threshold if rule else True
            rule_code = rule.code if rule else "RULE_MATCH"

            reason_str = (
                f"Rule {rule_code} triggered: Observed value '{matched.observed_value}' "
                f"{operator} expected threshold '{expected_val}' "
                f"(Risk Weight Contribution: +{matched.weight_contribution})"
            )

            # Construct Evidence References based on signal category
            evidence_refs: List[EvidenceReferenceModel] = []
            if sig:
                source_type = "SANCTION_LIST" if sig.category == "SANCTIONS" else "ON_CHAIN_TX"
                ref_uri = (
                    f"ofac://sanction-list/{assessment.target_address}"
                    if sig.category == "SANCTIONS"
                    else f"eip155:1/tx/{assessment.target_address}"
                )
                evidence_refs.append(
                    EvidenceReferenceModel(
                        source_type=source_type,
                        reference_uri=ref_uri,
                        observed_at=datetime.now(timezone.utc).isoformat(),
                        raw_payload_snippet=sig.metadata
                    )
                )

            quality_metrics = QualityMetricsModel(
                coverage=100.0,
                freshness_seconds=0,
                finality="FINAL",
                confidence=95.0
            )

            explained_signals.append(
                ExplainedSignalModel(
                    signal_id=matched.signal_id,
                    signal_code=matched.signal_code,
                    reason=reason_str,
                    observed_value=matched.observed_value,
                    operator=operator,
                    expected_value=expected_val,
                    contribution=matched.weight_contribution,
                    evidence_references=evidence_refs,
                    quality_metrics=quality_metrics
                )
            )

        reproducibility = ReproducibilityMetadataModel(
            dataset_snapshot_id="golden-dataset-snapshot-v1",
            feature_version="1.0.0",
            policy_version=policy.version,
            model_version="1.0.0",
            code_commit_hash=git_commit_hash,
            evaluated_at=assessment.evaluated_at
        )

        return AssessmentExplainabilityModel(
            explainability_id=str(uuid.uuid4()),
            assessment_id=assessment.event_id,
            target_address=assessment.target_address,
            final_risk_score=assessment.final_risk_score,
            risk_tier=assessment.risk_tier,
            explained_signals=explained_signals,
            reproducibility=reproducibility
        )
