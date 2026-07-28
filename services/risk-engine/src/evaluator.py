"""
Rule Evaluation Engine for cryptoAML Platform (F2-K2-A & F2-K2-B).
Evaluates signals against policy rules, accumulates weights, applies Cap/Floor limits,
handles Sanction Override Caps, maps to Risk Tiers, and generates Explainability reports.
"""

import uuid
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
try:
    from .models import (
        SignalModel,
        RuleModel,
        PolicyModel,
        CapFloorModel,
        TierModel,
        RiskTierEnum,
        RuleOperatorEnum,
        SeverityEnum,
        MatchedSignalSummaryModel,
        AssessmentEventModel,
        EvaluationRequest,
        EvaluationResponse
    )
    from .explainability import ExplainabilityGenerator
except ImportError:
    from models import (
        SignalModel,
        RuleModel,
        PolicyModel,
        CapFloorModel,
        TierModel,
        RiskTierEnum,
        RuleOperatorEnum,
        SeverityEnum,
        MatchedSignalSummaryModel,
        AssessmentEventModel,
        EvaluationRequest,
        EvaluationResponse
    )
    from explainability import ExplainabilityGenerator

logger = logging.getLogger("risk_engine")


class RuleEvaluator:
    def __init__(self):
        self.default_policy = self._build_default_policy()
        self.explainability_generator = ExplainabilityGenerator()

    def _build_default_policy(self) -> PolicyModel:
        """Constructs default enterprise risk policy if no custom policy is supplied."""
        rule_sanction_id = str(uuid.uuid4())
        rule_mixer_id = str(uuid.uuid4())

        rule_sanction = RuleModel(
            id=rule_sanction_id,
            code="RULE_SANCTION_MATCH",
            name="Sanctioned Entity Interaction",
            description="Triggered when target address interacts with OFAC/sanctioned list",
            signal_ids=["signal-sanctions"],
            operator=RuleOperatorEnum.EQUALS,
            threshold=True,
            weight={"rule_id": rule_sanction_id, "weight_value": 100.0},
            is_enabled=True
        )

        rule_mixer = RuleModel(
            id=rule_mixer_id,
            code="RULE_MIXER_USAGE",
            name="Mixer Protocol Interaction",
            description="Triggered when target interacts with Tornado Cash or known mixer",
            signal_ids=["signal-mixer"],
            operator=RuleOperatorEnum.EQUALS,
            threshold=True,
            weight={"rule_id": rule_mixer_id, "weight_value": 50.0},
            is_enabled=True
        )

        tiers = [
            TierModel(tier_name=RiskTierEnum.LOW, min_score=0.0, max_score=29.0),
            TierModel(tier_name=RiskTierEnum.MEDIUM, min_score=30.0, max_score=69.0),
            TierModel(tier_name=RiskTierEnum.HIGH, min_score=70.0, max_score=89.0),
            TierModel(tier_name=RiskTierEnum.CRITICAL, min_score=90.0, max_score=100.0)
        ]

        return PolicyModel(
            id=str(uuid.uuid4()),
            name="Default Enterprise Risk Policy",
            rules=[rule_sanction, rule_mixer],
            cap_floor=CapFloorModel(min_score_floor=0.0, max_score_cap=100.0, apply_sanction_override_cap=True),
            tiers=tiers,
            is_default=True
        )

    @staticmethod
    def evaluate_operator(observed: Any, operator: RuleOperatorEnum, threshold: Any) -> bool:
        """Evaluates a single rule operator condition against observed value."""
        if observed is None:
            return False

        try:
            if operator == RuleOperatorEnum.EQUALS:
                return observed == threshold
            elif operator == RuleOperatorEnum.NOT_EQUALS:
                return observed != threshold
            elif operator == RuleOperatorEnum.GREATER_THAN:
                return float(observed) > float(threshold)
            elif operator == RuleOperatorEnum.LESS_THAN:
                return float(observed) < float(threshold)
            elif operator == RuleOperatorEnum.CONTAINS:
                if isinstance(observed, (list, set, tuple, str)):
                    return threshold in observed
                return str(threshold) in str(observed)
            elif operator == RuleOperatorEnum.IN_LIST:
                if isinstance(threshold, (list, set, tuple)):
                    return observed in threshold
                return False
            elif operator == RuleOperatorEnum.EXISTS:
                return observed is not None and bool(observed)
            return False
        except Exception as e:
            logger.warning(f"Error evaluating operator {operator} on {observed} vs {threshold}: {e}")
            return False

    def map_score_to_tier(self, score: float, tiers: List[TierModel]) -> RiskTierEnum:
        """Maps numerical risk score (0-100) to corresponding Risk Tier."""
        for tier in tiers:
            if tier.min_score <= score <= tier.max_score:
                return tier.tier_name
        if score >= 90.0:
            return RiskTierEnum.CRITICAL
        elif score >= 70.0:
            return RiskTierEnum.HIGH
        elif score >= 30.0:
            return RiskTierEnum.MEDIUM
        return RiskTierEnum.LOW

    def evaluate_request(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Evaluates signals against policy rules, calculates risk score and tier,
        and builds the full AssessmentExplainabilityModel report.
        """
        corr_id = request.correlation_id or str(uuid.uuid4())
        policy = request.policy or self.default_policy

        if not request.target_address:
            return EvaluationResponse(success=False, error_message="Target address is required")

        signal_map: Dict[str, SignalModel] = {sig.id: sig for sig in request.signals}
        signal_code_map: Dict[str, SignalModel] = {sig.code: sig for sig in request.signals}

        matched_summaries: List[MatchedSignalSummaryModel] = []
        raw_accumulated_score = 0.0
        has_sanction_match = False

        for rule in policy.rules:
            if not rule.is_enabled:
                continue

            rule_triggered = False
            triggering_signal: Optional[SignalModel] = None

            # Check matching signals by ID or Code
            for sig_id in rule.signal_ids:
                sig = signal_map.get(sig_id) or signal_code_map.get(sig_id)
                if sig:
                    if self.evaluate_operator(sig.observed_value, rule.operator, rule.threshold):
                        rule_triggered = True
                        triggering_signal = sig
                        break

            if rule_triggered and triggering_signal:
                weight_val = rule.weight.weight_value
                raw_accumulated_score += weight_val

                if (
                    triggering_signal.category == "SANCTIONS"
                    or triggering_signal.severity == SeverityEnum.CRITICAL
                    or "SANCTION" in triggering_signal.code.upper()
                ):
                    has_sanction_match = True

                matched_summaries.append(
                    MatchedSignalSummaryModel(
                        signal_id=triggering_signal.id,
                        signal_code=triggering_signal.code,
                        severity=triggering_signal.severity,
                        observed_value=triggering_signal.observed_value,
                        weight_contribution=weight_val
                    )
                )

        # Apply Cap / Floor limits and Sanction Override Cap
        cap_floor = policy.cap_floor
        final_score = raw_accumulated_score

        if has_sanction_match and cap_floor.apply_sanction_override_cap:
            final_score = 100.0
        else:
            final_score = min(final_score, cap_floor.max_score_cap)
            final_score = max(final_score, cap_floor.min_score_floor)

        risk_tier = self.map_score_to_tier(final_score, policy.tiers)

        assessment = AssessmentEventModel(
            event_id=str(uuid.uuid4()),
            event_type="RISK_ASSESSMENT",
            target_address=request.target_address,
            chain=request.chain,
            final_risk_score=final_score,
            risk_tier=risk_tier,
            matched_signals=matched_summaries,
            policy_id=policy.id,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            correlation_id=corr_id
        )

        # Generate Explainability report
        explainability = self.explainability_generator.generate_explainability(
            assessment=assessment,
            policy=policy,
            signals=request.signals
        )

        return EvaluationResponse(
            success=True,
            assessment=assessment,
            explainability=explainability
        )
