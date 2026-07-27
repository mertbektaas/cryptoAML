"""
Canonical & Event Data Models for Python Normalizer Service.
Matches @crypto-aml/canonical-schema and @crypto-aml/event-contracts specifications.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, ConfigDict


class ChainNetwork(str, Enum):
    BITCOIN = "BITCOIN"
    ETHEREUM = "ETHEREUM"
    POLYGON = "POLYGON"
    ARBITRUM = "ARBITRUM"
    OPTIMISM = "OPTIMISM"
    AVALANCHE = "AVALANCHE"
    SOLANA = "SOLANA"
    BSC = "BSC"
    TRON = "TRON"


class EntityType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    EXCHANGE = "EXCHANGE"
    MIXER = "MIXER"
    SMART_CONTRACT = "SMART_CONTRACT"
    MINER = "MINER"
    UNKNOWN = "UNKNOWN"


class TokenType(str, Enum):
    NATIVE = "NATIVE"
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    SPL = "SPL"


class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    DECODE_FAILURE = "DECODE_FAILURE"


class AddressModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chain: ChainNetwork
    address: str
    entity_type: EntityType = EntityType.UNKNOWN
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    labels: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TokenModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chain: ChainNetwork
    contract_address: Optional[str] = None
    symbol: str
    name: str
    decimals: int = Field(default=18, ge=0, le=36)
    token_type: TokenType = TokenType.NATIVE
    schema_version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TokenTransferModel(BaseModel):
    token_address: Optional[str] = None
    from_address: str
    to_address: str
    amount: str  # Raw amount string (wei/satoshi)
    decimal_amount: float


class TransactionModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tx_hash: str
    chain: ChainNetwork
    block_number: int
    timestamp: str
    from_address: str
    to_address: Optional[str] = None
    value: str
    fee: str = "0"
    status: TransactionStatus = TransactionStatus.SUCCESS
    token_transfers: List[TokenTransferModel] = Field(default_factory=list)
    input_data: str = "0x"
    error_reason: Optional[str] = None
    schema_version: str = "1.0.0"


class SmartContractModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chain: ChainNetwork
    address: str
    creator_address: str
    creation_tx_hash: str
    is_verified: bool = False
    contract_type: str = "OTHER"
    bytecode_hash: Optional[str] = None
    schema_version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NormalizedMovementEventModel(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "TOKEN_MOVEMENT"
    chain: str
    transaction_hash: str
    block_number: int
    from_address: str
    to_address: str
    token_address: Optional[str] = None
    token_symbol: str = "ETH"
    raw_amount: str
    decimal_amount: float
    usd_value_at_timestamp: Optional[float] = None
    timestamp: str
    correlation_id: Optional[str] = None
    contract_version: str = "1.0.0"


class NormalizationResult(BaseModel):
    success: bool
    transaction: Optional[TransactionModel] = None
    movements: List[NormalizedMovementEventModel] = Field(default_factory=list)
    created_contract: Optional[SmartContractModel] = None
    addresses: List[AddressModel] = Field(default_factory=list)
    error_reason: Optional[str] = None
    correlation_id: Optional[str] = None
