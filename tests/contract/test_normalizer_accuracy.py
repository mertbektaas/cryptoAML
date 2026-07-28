"""
Accuracy & Contract Integration Test Suite for Normalizer Service (F1-K2-C).
Validates raw fixtures against Golden Datasets ensuring zero regression,
accurate token movement decoding, contract creation detection, and decode failure isolation.
"""

import os
import unittest
import yaml
from services.normalizer.src.normalizer import NormalizerEngine
from services.normalizer.src.models import TransactionStatus

# Resolve paths to tests/fixtures and tests/golden-datasets
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_FIXTURES_PATH = os.path.join(ROOT_DIR, "tests", "fixtures", "raw-transactions.yaml")
GOLDEN_DATASETS_PATH = os.path.join(ROOT_DIR, "tests", "golden-datasets", "normalized-movements.yaml")


class TestNormalizerAccuracyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = NormalizerEngine()

        # Load raw fixtures
        with open(RAW_FIXTURES_PATH, "r", encoding="utf-8") as f:
            cls.raw_data = yaml.safe_load(f)

        # Load golden datasets
        with open(GOLDEN_DATASETS_PATH, "r", encoding="utf-8") as f:
            cls.golden_data = yaml.safe_load(f)

    def test_native_transfer_accuracy(self):
        """Validates Native ETH transfer raw fixture against golden output."""
        raw_tx = self.raw_data["fixtures"]["native_transfer"]
        golden = self.golden_data["golden_outputs"]["native_transfer_golden"]

        result = self.engine.normalize_raw_payload(raw_tx)

        self.assertTrue(result.success, "Native transfer normalization must succeed")
        self.assertEqual(len(result.movements), 1, "Exactly one native movement expected")

        mv = result.movements[0]
        self.assertEqual(mv.chain, golden["chain"])
        self.assertEqual(mv.transaction_hash, golden["transactionHash"])
        self.assertEqual(mv.from_address, golden["fromAddress"])
        self.assertEqual(mv.to_address, golden["toAddress"])
        self.assertEqual(mv.token_symbol, golden["tokenSymbol"])
        self.assertEqual(mv.decimal_amount, golden["decimalAmount"])

    def test_erc20_transfer_accuracy(self):
        """Validates ERC-20 USDT transfer raw fixture against golden output."""
        raw_tx = self.raw_data["fixtures"]["erc20_transfer"]
        golden = self.golden_data["golden_outputs"]["erc20_transfer_golden"]

        result = self.engine.normalize_raw_payload(raw_tx)

        self.assertTrue(result.success, "ERC-20 transfer normalization must succeed")
        self.assertEqual(len(result.movements), 1, "Exactly one ERC-20 movement expected")

        mv = result.movements[0]
        self.assertEqual(mv.chain, golden["chain"])
        self.assertEqual(mv.transaction_hash, golden["transactionHash"])
        self.assertEqual(mv.from_address, golden["fromAddress"])
        self.assertEqual(mv.to_address, golden["toAddress"])
        self.assertEqual(mv.token_address, golden["tokenAddress"])
        self.assertEqual(mv.token_symbol, golden["tokenSymbol"])
        self.assertEqual(mv.decimal_amount, golden["decimalAmount"])

    def test_contract_creation_accuracy(self):
        """Validates Smart Contract creation raw fixture against golden record."""
        raw_tx = self.raw_data["fixtures"]["contract_creation"]
        golden = self.golden_data["golden_outputs"]["contract_creation_golden"]

        result = self.engine.normalize_raw_payload(raw_tx)

        self.assertTrue(result.success, "Contract creation normalization must succeed")
        self.assertIsNotNone(result.created_contract, "Created contract model must be populated")

        c = result.created_contract
        self.assertEqual(c.chain.value, golden["chain"])
        self.assertEqual(c.address, golden["address"])
        self.assertEqual(c.creator_address, golden["creatorAddress"])
        self.assertEqual(c.creation_tx_hash, golden["creationTxHash"])

    def test_decode_failure_isolation(self):
        """Validates decode failure isolation and error reporting against golden record."""
        raw_tx = self.raw_data["fixtures"]["decode_failure"]
        golden = self.golden_data["golden_outputs"]["decode_failure_golden"]

        result = self.engine.normalize_raw_payload(raw_tx)

        self.assertFalse(result.success, "Decode failure payload must return success=False")
        self.assertIsNotNone(result.transaction, "Failed transaction record must be retained")
        self.assertEqual(result.transaction.status, TransactionStatus.DECODE_FAILURE)
        self.assertIn("EVMSimulationError", result.error_reason)
        self.assertEqual(result.transaction.error_reason, golden["errorReason"])

    def test_idempotency_contract(self):
        """Validates idempotent processing when same raw transaction is ingested twice."""
        raw_tx = self.raw_data["fixtures"]["native_transfer"]

        # First ingestion
        res1 = self.engine.normalize_raw_payload(raw_tx)
        self.assertTrue(res1.success)

        # Duplicate second ingestion (must complete gracefully without error)
        res2 = self.engine.normalize_raw_payload(raw_tx)
        self.assertTrue(res2.success)


if __name__ == "__main__":
    unittest.main()
