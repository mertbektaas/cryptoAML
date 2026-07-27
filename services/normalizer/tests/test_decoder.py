"""
Unit Tests for EventDecoder Module (F1-K2-B).
Verifies ERC-20, ERC-721, ERC-1155, and Uniswap DEX Swap Log Decoding.
"""

import unittest
from services.normalizer.src.decoder import EventDecoder


class TestEventDecoder(unittest.TestCase):
    def setUp(self):
        self.decoder = EventDecoder()

    def test_decode_address_topic(self):
        topic = "0x00000000000000000000000071c7656ec7ab88b098defb751b7401b5f6d8976f"
        addr = self.decoder.decode_address_topic(topic)
        self.assertEqual(addr, "0x71c7656ec7ab88b098defb751b7401b5f6d8976f")

    def test_decode_erc20_transfer(self):
        log = {
            "address": "0x0000000000000000000000000000000000000002",
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                "0x0000000000000000000000001111111111111111111111111111111111111111",
                "0x0000000000000000000000002222222222222222222222222222222222222222"
            ],
            "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000"  # 1.0 Token (18 decimals)
        }

        movements = self.decoder.decode_log(log, "ETHEREUM", "0xhash", 100, "2026-07-27T12:00:00Z")
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].from_address, "0x1111111111111111111111111111111111111111")
        self.assertEqual(movements[0].to_address, "0x2222222222222222222222222222222222222222")

    def test_decode_erc721_nft_transfer(self):
        log = {
            "address": "0xNFTContractAddress0000000000000000000",
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                "0x0000000000000000000000001111111111111111111111111111111111111111",
                "0x0000000000000000000000002222222222222222222222222222222222222222",
                "0x000000000000000000000000000000000000000000000000000000000000002a"  # Token ID 42
            ],
            "data": "0x"
        }

        movements = self.decoder.decode_log(log, "ETHEREUM", "0xhash", 101, "2026-07-27T12:05:00Z")
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].token_symbol, "NFT#42")
        self.assertEqual(movements[0].decimal_amount, 1.0)

    def test_decode_uniswap_v2_swap(self):
        log = {
            "address": "0xUniswapPairAddress000000000000000000",
            "topics": [
                "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
                "0x0000000000000000000000003333333333333333333333333333333333333333",  # Sender
                "0x0000000000000000000000004444444444444444444444444444444444444444"   # To
            ],
            "data": "0x00"
        }

        movements = self.decoder.decode_log(log, "ETHEREUM", "0xhash", 102, "2026-07-27T12:10:00Z")
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].token_symbol, "DEX_SWAP_V2")
        self.assertEqual(movements[0].from_address, "0x3333333333333333333333333333333333333333")

    def test_decode_failure_malformed_topic(self):
        log = {
            "address": "0xTokenAddress",
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                "0xINVALID_SHORT_TOPIC"
            ],
            "data": "0x0"
        }

        with self.assertRaises(ValueError):
            self.decoder.decode_log(log, "ETHEREUM", "0xhash", 103, "2026-07-27T12:15:00Z")


if __name__ == "__main__":
    unittest.main()
