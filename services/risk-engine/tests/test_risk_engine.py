"""
Comprehensive Unit Test Suite for Risk Engine Service (F2-K2-A).
Verifies Rule Operators, Weight Accumulation, Sanction Override Cap, and Tier Mapping.
"""

import sys
import os
import unittest

# Insert src directory to PYTHONPATH for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from models import (
    SignalModel,
    RuleModel,
    PolicyModel,
    WeightModel,
    CapFloorModel,
    TierModel,
    SeverityEnum,
    RuleOperatorEnum,
    RiskTierEnum,
    EvaluationRequest
)
from evaluator import RuleEvaluator


class TestRiskEngineEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = RuleEvaluator()

    def test_evaluate_operators(self):
        """Validates all RuleOperatorEnum condition evaluations."""
        # EQUALS
        self.assertTrue(RuleEvaluator.evaluate_operator(True, RuleOperatorEnum.EQUALS, True))
        self.assertFalse(RuleEvaluator.evaluate_operator(False, RuleOperatorEnum.EQUALS, True))

        # NOT_EQUALS
        self.assertTrue(RuleEvaluator.evaluate_operator("EXCHANGE", RuleOperatorEnum.NOT_EQUALS, "MIXER"))

        # GREATER_THAN
        self.assertTrue(RuleEvaluator.evaluate_operator(15000, RuleOperatorEnum.GREATER_THAN, 10000))
        self.assertFalse(RuleEvaluator.evaluate_operator(5000, RuleOperatorEnum.GREATER_THAN, 10000))

        # LESS_THAN
        self.assertTrue(RuleEvaluator.evaluate_operator(50, RuleOperatorEnum.LESS_THAN, 100))

        # CONTAINS
        self.assertTrue(RuleEvaluator.evaluate_operator(["binance", "hot-wallet"], RuleOperatorEnum.CONTAINS, "binance"))

        # IN_LIST
        self.assertTrue(RuleEvaluator.evaluate_operator("OFAC", RuleOperatorEnum.IN_LIST, ["OFAC", "EU", "UN"]))

        # EXISTS
        self.assertTrue(RuleEvaluator.evaluate_operator({"list": "OFAC"}, RuleOperatorEnum.EXISTS, None))
        self.assertFalse(RuleEvaluator.evaluate_operator(None, RuleOperatorEnum.EXISTS, None))

    def test_weight_accumulation_and_tier_mapping(self):
        """Validates that rule weights accumulate and map to expected Risk Tier."""
        sig1 = SignalModel(id="sig-1", code="MIXER_EXPOSURE", category="MIXER", severity=SeverityEnum.HIGH, observed_value=True)
        sig2 = SignalModel(id="sig-2", code="HIGH_VOLUME", category="HIGH_VOLUME", severity=SeverityEnum.MEDIUM, observed_value=15000)

        rule1 = RuleModel(
            id="rule-1",
            code="RULE_MIXER",
            name="Mixer Rule",
            signal_ids=["sig-1"],
            operator=RuleOperatorEnum.EQUALS,
            threshold=True,
            weight=WeightModel(rule_id="rule-1", weight_value=50.0)
        )

        rule2 = RuleModel(
            id="rule-2",
            code="RULE_VOLUME",
            name="Volume Rule",
            signal_ids=["sig-2"],
            operator=RuleOperatorEnum.GREATER_THAN,
            threshold=10000,
            weight=WeightModel(rule_id="rule-2", weight_value=30.0)
        )

        policy = PolicyModel(
            name="Custom Test Policy",
            rules=[rule1, rule2],
            tiers=[
                TierModel(tier_name=RiskTierEnum.LOW, min_score=0.0, max_score=29.0),
                TierModel(tier_name=RiskTierEnum.MEDIUM, min_score=30.0, max_score=69.0),
                TierModel(tier_name=RiskTierEnum.HIGH, min_score=70.0, max_score=89.0),
                TierModel(tier_name=RiskTierEnum.CRITICAL, min_score=90.0, max_score=100.0)
            ]
        )

        req = EvaluationRequest(
            target_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
            signals=[sig1, sig2],
            policy=policy
        )

        res = self.evaluator.evaluate_request(req)
        self.assertTrue(res.success)
        self.assertIsNotNone(res.assessment)
        self.assertEqual(res.assessment.final_risk_score, 80.0)  # 50 + 30
        self.assertEqual(res.assessment.risk_tier, RiskTierEnum.HIGH)
        self.assertEqual(len(res.assessment.matched_signals), 2)

    def test_sanction_override_cap(self):
        """Validates that a sanction match triggers Sanction Override Cap to 100 (CRITICAL)."""
        sanction_sig = SignalModel(
            id="sig-sanction",
            code="SANCTION_MATCH",
            category="SANCTIONS",
            severity=SeverityEnum.CRITICAL,
            observed_value=True
        )

        rule_sanction = RuleModel(
            id="rule-sanction",
            code="RULE_SANCTION",
            name="Sanction Rule",
            signal_ids=["sig-sanction"],
            operator=RuleOperatorEnum.EQUALS,
            threshold=True,
            weight=WeightModel(rule_id="rule-sanction", weight_value=40.0)
        )

        policy = PolicyModel(
            name="Sanction Cap Policy",
            rules=[rule_sanction],
            cap_floor=CapFloorModel(apply_sanction_override_cap=True),
            tiers=[
                TierModel(tier_name=RiskTierEnum.LOW, min_score=0.0, max_score=29.0),
                TierModel(tier_name=RiskTierEnum.CRITICAL, min_score=90.0, max_score=100.0)
            ]
        )

        req = EvaluationRequest(
            target_address="0xSanctionedTargetAddress",
            signals=[sanction_sig],
            policy=policy
        )

        res = self.evaluator.evaluate_request(req)
        self.assertTrue(res.success)
        self.assertEqual(res.assessment.final_risk_score, 100.0)
        self.assertEqual(res.assessment.risk_tier, RiskTierEnum.CRITICAL)


if __name__ == "__main__":
    unittest.main()
