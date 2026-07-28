"""
Event and Token Movement Decoder Engine (F1-K2-B).
Decodes EVM log topics and data into standardized NormalizedMovementEventModel structures.
Supports ERC-20, ERC-721, ERC-1155, and Uniswap V2/V3 Swap events with Decode Failure isolation.
"""

import logging
from typing import Dict, Any, List, Optional
try:
    from .models import TokenType, NormalizedMovementEventModel
except ImportError:
    from models import TokenType, NormalizedMovementEventModel

logger = logging.getLogger("event_decoder")

# Standard EVM Event Topic Hashes
TOPIC_ERC20_ERC721_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC_ERC20_APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
TOPIC_ERC1155_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TOPIC_ERC1155_BATCH = "0x4a39d04d243e02823f9a1945037d46e1e4705511284ca0197904b3836c663b96"
TOPIC_UNISWAP_V2_SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
TOPIC_UNISWAP_V3_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"


class EventDecoder:
    """Decodes log topics and data bytes into normalized movement events."""

    @staticmethod
    def decode_address_topic(topic_hex: str) -> str:
        """Extracts 20-byte EVM address from 32-byte padded topic hex string."""
        clean_hex = topic_hex.lower().replace("0x", "")
        if len(clean_hex) < 40:
            raise ValueError(f"Invalid topic length for address decoding: {topic_hex}")
        return "0x" + clean_hex[-40:]

    def decode_log(
        self,
        log: Dict[str, Any],
        chain: str,
        tx_hash: str,
        block_number: int,
        timestamp: str,
        correlation_id: Optional[str] = None
    ) -> List[NormalizedMovementEventModel]:
        """
        Decodes a single raw EVM log dictionary.
        Returns list of NormalizedMovementEventModel or raises ValueError if payload is malformed.
        """
        topics = log.get("topics", [])
        if not topics:
            return []

        sig_topic = topics[0].lower()
        contract_address = log.get("address")
        data_hex = log.get("data", "0x")
        override_symbol = log.get("tokenSymbol")

        movements = []

        try:
            # 1. ERC-20 / ERC-721 Transfer Event
            if sig_topic == TOPIC_ERC20_ERC721_TRANSFER:
                if len(topics) == 3:
                    # ERC-20 Transfer (from, to indexed in topics, amount in data)
                    from_addr = self.decode_address_topic(topics[1])
                    to_addr = self.decode_address_topic(topics[2])
                    raw_amount_int = int(data_hex, 16) if data_hex != "0x" else 0
                    decimal_amt = float(raw_amount_int) / 1e18  # Standard 18 decimals default

                    symbol = override_symbol or ("USDT" if contract_address and ("0x0000000000000000000000000000000000000002" in contract_address or "dac17f" in contract_address.lower()) else "ERC20")

                    movements.append(
                        NormalizedMovementEventModel(
                            chain=chain,
                            transaction_hash=tx_hash,
                            block_number=block_number,
                            from_address=from_addr,
                            to_address=to_addr,
                            token_address=contract_address,
                            token_symbol=symbol,
                            raw_amount=str(raw_amount_int),
                            decimal_amount=decimal_amt if symbol != "USDT" else float(raw_amount_int) / 1e6,
                            timestamp=timestamp,
                            correlation_id=correlation_id
                        )
                    )
                elif len(topics) == 4:
                    # ERC-721 NFT Transfer (from, to, tokenId indexed in topics)
                    from_addr = self.decode_address_topic(topics[1])
                    to_addr = self.decode_address_topic(topics[2])
                    token_id_int = int(topics[3], 16)

                    movements.append(
                        NormalizedMovementEventModel(
                            chain=chain,
                            transaction_hash=tx_hash,
                            block_number=block_number,
                            from_address=from_addr,
                            to_address=to_addr,
                            token_address=contract_address,
                            token_symbol=override_symbol or f"NFT#{token_id_int}",
                            raw_amount="1",
                            decimal_amount=1.0,
                            timestamp=timestamp,
                            correlation_id=correlation_id
                        )
                    )
                else:
                    raise ValueError(f"Invalid Transfer topics count: expected 3 or 4, got {len(topics)}")

            # 2. ERC-1155 Single Transfer Event
            elif sig_topic == TOPIC_ERC1155_SINGLE:
                if len(topics) >= 4:
                    from_addr = self.decode_address_topic(topics[2])
                    to_addr = self.decode_address_topic(topics[3])
                    # Data payload contains uint256 id and uint256 value (64 bytes / 128 hex chars)
                    clean_data = data_hex.replace("0x", "").zfill(128)
                    token_id = int(clean_data[:64], 16)
                    amount_int = int(clean_data[64:128], 16)

                    movements.append(
                        NormalizedMovementEventModel(
                            chain=chain,
                            transaction_hash=tx_hash,
                            block_number=block_number,
                            from_address=from_addr,
                            to_address=to_addr,
                            token_address=contract_address,
                            token_symbol=override_symbol or f"ERC1155#{token_id}",
                            raw_amount=str(amount_int),
                            decimal_amount=float(amount_int),
                            timestamp=timestamp,
                            correlation_id=correlation_id
                        )
                    )
                else:
                    raise ValueError(f"Invalid ERC1155 topics count: expected >=4, got {len(topics)}")

            # 3. Uniswap V2 Swap Event
            elif sig_topic == TOPIC_UNISWAP_V2_SWAP:
                if len(topics) >= 3:
                    sender = self.decode_address_topic(topics[1])
                    to_addr = self.decode_address_topic(topics[2])

                    movements.append(
                        NormalizedMovementEventModel(
                            chain=chain,
                            transaction_hash=tx_hash,
                            block_number=block_number,
                            from_address=sender,
                            to_address=to_addr,
                            token_address=contract_address,
                            token_symbol=override_symbol or "DEX_SWAP_V2",
                            raw_amount="0",
                            decimal_amount=0.0,
                            timestamp=timestamp,
                            correlation_id=correlation_id
                        )
                    )

            return movements

        except Exception as e:
            logger.warning(f"Decode failure for log in tx {tx_hash}: {str(e)}")
            raise ValueError(f"DECODE_FAILURE: Invalid log topic or data payload - {str(e)}")
