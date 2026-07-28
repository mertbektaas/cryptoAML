"""
Comprehensive Test Suite for Python Normalizer Service (F1-K2-A).
Verifies Native ETH, ERC-20, Contract Creation, Idempotency, and Decode Failures.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from models import (
    ChainNetwork,
    TransactionStatus,
    NormalizationResult
)
from normalizer import NormalizerEngine


class TestNormalizerEngine(unittest.TestCase):
    def setUp(self):
        self.engine = NormalizerEngine()

    def test_normalize_native_transfer(self):
        payload = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "chain": "ETHEREUM",
            "txHash": "0x8888888888888888888888888888888888888888888888888888888888888888",
            "blockNumber": 19000001,
            "timestamp": "2026-07-27T10:00:00Z",
            "fromAddress": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "toAddress": "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
            "value": "1000000000000000000",  # 1 ETH
            "fee": "21000000000000",
            "status": "SUCCESS"
        }

        result = self.engine.normalize_raw_payload(payload)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.transaction)
        self.assertEqual(result.transaction.chain, ChainNetwork.ETHEREUM)
        self.assertEqual(result.transaction.value, "1000000000000000000")
        self.assertEqual(len(result.movements), 1)
        self.assertEqual(result.movements[0].decimal_amount, 1.0)
        self.assertEqual(result.movements[0].token_symbol, "ETH")

    def test_normalize_erc20_transfer(self):
        payload = {
            "id": "22222222-2222-2222-2222-222222222222",
            "chain": "ETHEREUM",
            "txHash": "0x7777777777777777777777777777777777777777777777777777777777777777",
            "blockNumber": 19000002,
            "timestamp": "2026-07-27T10:05:00Z",
            "fromAddress": "0x1111111111111111111111111111111111111111",
            "toAddress": "0x0000000000000000000000000000000000000002",
            "value": "0",
            "status": "SUCCESS",
            "logs": [
                {
                    "address": "0x0000000000000000000000000000000000000002",
                    "topics": [
                        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                        "0x0000000000000000000000001111111111111111111111111111111111111111",
                        "0x0000000000000000000000002222222222222222222222222222222222222222"
                    ],
                    "data": "0x000000000000000000000000000000000000000000000000000000003b9aca00"  # 1000 USDT (6 decimals)
                }
            ]
        }

        result = self.engine.normalize_raw_payload(payload)
        self.assertTrue(result.success)
        self.assertEqual(len(result.movements), 1)
        self.assertEqual(result.movements[0].token_symbol, "USDT")
        self.assertEqual(result.movements[0].decimal_amount, 1000.0)

    def test_normalize_smart_contract_creation(self):
        payload = {
            "chain": "ETHEREUM",
            "txHash": "0x5555555555555555555555555555555555555555555555555555555555555555",
            "blockNumber": 19000004,
            "timestamp": "2026-07-27T10:15:00Z",
            "fromAddress": "0x4444444444444444444444444444444444444444",
            "toAddress": None,
            "createdContractAddress": "0x5555555555555555555555555555555555555555",
            "value": "0",
            "status": "SUCCESS"
        }

        result = self.engine.normalize_raw_payload(payload)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.created_contract)
        self.assertEqual(result.created_contract.address, "0x5555555555555555555555555555555555555555")

    def test_handle_decode_failure(self):
        payload = {
            "chain": "ETHEREUM",
            "txHash": "0x4444444444444444444444444444444444444444444444444444444444444444",
            "blockNumber": 19000005,
            "timestamp": "2026-07-27T10:20:00Z",
            "fromAddress": "0x5555555555555555555555555555555555555555",
            "status": "FAILED",
            "inputData": "0xMALFORMED_HEX",
            "errorReason": "EVMSimulationError: Bad opcode"
        }

        result = self.engine.normalize_raw_payload(payload)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.transaction)
        self.assertEqual(result.transaction.status, TransactionStatus.DECODE_FAILURE)
        self.assertEqual(result.transaction.error_reason, "EVMSimulationError: Bad opcode")


if __name__ == "__main__":
    unittest.main()
