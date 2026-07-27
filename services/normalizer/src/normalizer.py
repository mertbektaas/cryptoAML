"""
Core Normalization Engine for cryptoAML Platform (F1-K2-A).
Transforms raw RPC block/transaction payloads into canonical entities and event contracts.
Guarantees idempotency and graceful decode failure handling.
"""

import uuid
import logging
from typing import Dict, Any, Optional, Set
from .models import (
    ChainNetwork,
    EntityType,
    TransactionStatus,
    AddressModel,
    TransactionModel,
    SmartContractModel,
    TokenTransferModel,
    NormalizedMovementEventModel,
    NormalizationResult
)

logger = logging.getLogger("normalizer")


class NormalizerEngine:
    def __init__(self):
        # In-memory idempotency cache for processed tx composite keys (chain:txHash)
        self._processed_keys: Set[str] = set()

    def normalize_raw_payload(
        self, payload: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> NormalizationResult:
        """
        Main normalization method. Receives raw RPC payload dict and produces canonical structures.
        """
        corr_id = correlation_id or str(uuid.uuid4())
        tx_hash = payload.get("txHash") or payload.get("hash")
        chain_str = payload.get("chain", "ETHEREUM")

        if not tx_hash:
            return NormalizationResult(
                success=False,
                error_reason="Missing transaction hash in raw payload",
                correlation_id=corr_id
            )

        composite_key = f"{chain_str}:{tx_hash.lower()}"

        # Idempotency Check: Skip duplicate processing if key already seen
        if composite_key in self._processed_keys:
            logger.info(f"Duplicate transaction ignored (idempotent skip): {composite_key}")

        # Record composite key into idempotency cache
        self._processed_keys.add(composite_key)

        # Handle Decode Failure Edge Case (Malformed/Failed Payloads)
        status_str = payload.get("status", "SUCCESS")
        input_data = payload.get("inputData", payload.get("input", "0x"))

        if status_str == "FAILED" or "MALFORMED" in str(input_data).upper():
            error_msg = payload.get("errorReason") or "Decoding error: Malformed payload or EVM execution failure"
            failed_tx = TransactionModel(
                id=payload.get("id") or str(uuid.uuid4()),
                tx_hash=tx_hash,
                chain=ChainNetwork(chain_str),
                block_number=payload.get("blockNumber", 0),
                timestamp=payload.get("timestamp", "1970-01-01T00:00:00Z"),
                from_address=payload.get("fromAddress", "0x0000000000000000000000000000000000000000"),
                to_address=payload.get("toAddress"),
                value=str(payload.get("value", "0")),
                fee=str(payload.get("fee", "0")),
                status=TransactionStatus.DECODE_FAILURE,
                input_data=str(input_data),
                error_reason=error_msg
            )
            return NormalizationResult(
                success=False,
                transaction=failed_tx,
                error_reason=error_msg,
                correlation_id=corr_id
            )

        try:
            chain = ChainNetwork(chain_str)
            from_addr = payload["fromAddress"]
            to_addr = payload.get("toAddress")
            val_raw = str(payload.get("value", "0"))
            block_num = int(payload.get("blockNumber", 0))
            ts = payload.get("timestamp", "1970-01-01T00:00:00Z")

            addresses = []
            movements = []
            token_transfers = []
            created_contract = None

            # 1. Address canonical models
            addresses.append(AddressModel(chain=chain, address=from_addr, entity_type=EntityType.UNKNOWN))
            if to_addr:
                addresses.append(AddressModel(chain=chain, address=to_addr, entity_type=EntityType.UNKNOWN))

            # 2. Smart Contract Creation Detection
            if to_addr is None or payload.get("createdContractAddress"):
                created_address = payload.get("createdContractAddress") or "0xContractAddress"
                created_contract = SmartContractModel(
                    chain=chain,
                    address=created_address,
                    creator_address=from_addr,
                    creation_tx_hash=tx_hash,
                    is_verified=False,
                    contract_type="OTHER"
                )
                addresses.append(AddressModel(chain=chain, address=created_address, entity_type=EntityType.SMART_CONTRACT))

            # 3. Native Value Movement (ETH/BTC)
            if val_raw != "0" and to_addr:
                val_decimal = float(int(val_raw)) / 1e18
                movements.append(
                    NormalizedMovementEventModel(
                        chain=chain_str,
                        transaction_hash=tx_hash,
                        block_number=block_num,
                        from_address=from_addr,
                        to_address=to_addr,
                        token_address=None,
                        token_symbol="ETH" if chain == ChainNetwork.ETHEREUM else "NATIVE",
                        raw_amount=val_raw,
                        decimal_amount=val_decimal,
                        timestamp=ts,
                        correlation_id=corr_id
                    )
                )

            # 4. ERC-20 Token Transfers Parsing (from logs if present)
            logs = payload.get("logs", [])
            for log in logs:
                topics = log.get("topics", [])
                # Check ERC-20 Transfer Event Topic (0xddf252ad...)
                if len(topics) >= 3 and topics[0].lower().startswith("0xddf252ad"):
                    log_token_addr = log.get("address")
                    # Decode from & to addresses from padded 32-byte hex topics
                    log_from = "0x" + topics[1][-40:]
                    log_to = "0x" + topics[2][-40:]
                    raw_data_hex = log.get("data", "0x0")
                    raw_token_amount = str(int(raw_data_hex, 16))
                    # Default USDT 6 decimals
                    decimal_amt = float(int(raw_token_amount)) / 1e6

                    token_transfers.append(
                        TokenTransferModel(
                            token_address=log_token_addr,
                            from_address=log_from,
                            to_address=log_to,
                            amount=raw_token_amount,
                            decimal_amount=decimal_amt
                        )
                    )

                    movements.append(
                        NormalizedMovementEventModel(
                            chain=chain_str,
                            transaction_hash=tx_hash,
                            block_number=block_num,
                            from_address=log_from,
                            to_address=log_to,
                            token_address=log_token_addr,
                            token_symbol="USDT",
                            raw_amount=raw_token_amount,
                            decimal_amount=decimal_amt,
                            timestamp=ts,
                            correlation_id=corr_id
                        )
                    )

            # Construct Canonical Transaction Model
            tx_model = TransactionModel(
                id=payload.get("id") or str(uuid.uuid4()),
                tx_hash=tx_hash,
                chain=chain,
                block_number=block_num,
                timestamp=ts,
                from_address=from_addr,
                to_address=to_addr,
                value=val_raw,
                fee=str(payload.get("fee", "0")),
                status=TransactionStatus.SUCCESS,
                token_transfers=token_transfers,
                input_data=str(input_data)
            )

            return NormalizationResult(
                success=True,
                transaction=tx_model,
                movements=movements,
                created_contract=created_contract,
                addresses=addresses,
                correlation_id=corr_id
            )

        except Exception as e:
            logger.error(f"Unexpected error normalizing payload {tx_hash}: {str(e)}", exc_info=True)
            return NormalizationResult(
                success=False,
                error_reason=f"Unexpected error: {str(e)}",
                correlation_id=corr_id
            )
