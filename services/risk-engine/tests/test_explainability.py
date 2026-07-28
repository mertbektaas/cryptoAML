"""
Unit Tests for Explainability Engine (F2-K2-B).
Verifies Evidence -> Signal -> Assessment chain, quality metrics, and reproducibility metadata.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from models import (
    SignalModel,
    RuleModel,
    PolicyModel,
    WeightModel,
    SeverityEnum,
    RuleOperatorEnum,
    RiskTierEnum,
    EvaluationRequest
)
from evaluator import RuleEvaluator
from explainability import ExplainabilityGenerator


class TestExplainabilityEngine(unittest.TestCase):
    def setUp(self):
        self.evaluator = RuleEvaluator()
        self.generator = ExplainabilityGenerator()

    def test_explainability_chain_generation(self):
        """Validates that EvaluationResponse includes complete AssessmentExplainabilityModel."""
        sanction_sig = SignalModel(
            id="sig-sanction-100",
            code="SANCTION_EXPOSURE",
            name="Sanction Signal",
            category="SANCTIONS",
            severity=SeverityEnum.CRITICAL,
            observed_value=True,
            metadata={"sourceList": "OFAC_SDN"}
        )

        rule = RuleModel(
            id="rule-sanction-100",
            code="RULE_SANCTION_MATCH",
            name="Sanction Matching Rule",
            signal_ids=["sig-sanction-100"],
            operator=RuleOperatorEnum.EQUALS,
            threshold=True,
            weight=WeightModel(rule_id="rule-sanction-100", weight_value=100.0)
        )

        policy = PolicyModel(
            name="Explainability Test Policy",
            rules=[rule]
        )

        req = EvaluationRequest(
            target_address="0xSanctionedAddress123",
            signals=[sanction_sig],
            policy=policy
        )

        res = self.evaluator.evaluate_request(req)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.assessment)
        self.assertIsNotNone(res.explainability)

        exp = res.explainability
        self.assertEqual(exp.assessment_id, res.assessment.event_id)
        self.assertEqual(exp.target_address, "0xSanctionedAddress123")
        self.assertEqual(exp.final_risk_score, 100.0)
        self.assertEqual(exp.risk_tier, RiskTierEnum.CRITICAL)

        # Validate Explained Signal Details
        self.assertEqual(len(exp.explained_signals), 1)
        explained_sig = exp.explained_signals[0]
        self.assertEqual(explained_sig.signal_code, "SANCTION_EXPOSURE")
        self.assertIn("RULE_SANCTION_MATCH", explained_sig.reason)
        self.assertEqual(explained_sig.contribution, 100.0)

        # Validate Evidence Reference
        self.assertEqual(len(explained_sig.evidence_references), 1)
        evidence = explained_sig.evidence_references[0]
        self.assertEqual(evidence.source_type, "SANCTION_LIST")
        self.assertIn("ofac://", evidence.reference_uri)

        # Validate Quality Metrics
        self.assertEqual(explained_sig.quality_metrics.coverage, 100.0)
        self.assertEqual(explained_sig.quality_metrics.finality, "FINAL")

        # Validate Reproducibility Metadata
        self.assertEqual(exp.reproducibility.policy_version, policy.version)
        self.assertIsNotNone(exp.reproducibility.evaluated_at)


if __name__ == "__main__":
    unittest.main()
