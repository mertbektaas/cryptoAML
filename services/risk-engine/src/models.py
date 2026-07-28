"""
Pydantic v2 Data Models for Risk Engine Service (F2-K2-A).
Matches @crypto-aml/policy-schema and @crypto-aml/event-contracts specifications.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, ConfigDict


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleOperatorEnum(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    CONTAINS = "CONTAINS"
    IN_LIST = "IN_LIST"
    EXISTS = "EXISTS"


class RiskTierEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionRequiredEnum(str, Enum):
    NONE = "NONE"
    MONITOR = "MONITOR"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCK_IMMEDIATELY = "BLOCK_IMMEDIATELY"


class SignalModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str = ""
    category: str = "CUSTOM"
    severity: SeverityEnum = SeverityEnum.MEDIUM
    observed_value: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0.0"


class WeightModel(BaseModel):
    rule_id: str
    weight_value: float = Field(default=0.0, ge=0.0, le=100.0)
    adjustment_reason: Optional[str] = None
    schema_version: str = "1.0.0"


class RuleModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: str = ""
    signal_ids: List[str] = Field(default_factory=list)
    operator: RuleOperatorEnum
    threshold: Any = None
    weight: WeightModel
    is_enabled: bool = True
    schema_version: str = "1.0.0"


class CapFloorModel(BaseModel):
    min_score_floor: float = Field(default=0.0, ge=0.0, le=100.0)
    max_score_cap: float = Field(default=100.0, ge=0.0, le=100.0)
    apply_sanction_override_cap: bool = True
    schema_version: str = "1.0.0"


class TierModel(BaseModel):
    tier_name: RiskTierEnum
    min_score: float = Field(ge=0.0, le=100.0)
    max_score: float = Field(ge=0.0, le=100.0)
    action_required: ActionRequiredEnum = ActionRequiredEnum.NONE
    description: Optional[str] = None
    schema_version: str = "1.0.0"


class PolicyModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: str = ""
    rules: List[RuleModel] = Field(default_factory=list)
    cap_floor: CapFloorModel = Field(default_factory=CapFloorModel)
    tiers: List[TierModel] = Field(default_factory=list)
    is_default: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MatchedSignalSummaryModel(BaseModel):
    signal_id: str
    signal_code: str
    severity: SeverityEnum
    observed_value: Any
    weight_contribution: float


class AssessmentEventModel(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "RISK_ASSESSMENT"
    target_address: str
    chain: str = "ETHEREUM"
    final_risk_score: float = Field(ge=0.0, le=100.0)
    risk_tier: RiskTierEnum
    matched_signals: List[MatchedSignalSummaryModel] = Field(default_factory=list)
    policy_id: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    contract_version: str = "1.0.0"


class EvaluationRequest(BaseModel):
    target_address: str
    chain: str = "ETHEREUM"
    signals: List[SignalModel] = Field(default_factory=list)
    policy: Optional[PolicyModel] = None
    correlation_id: Optional[str] = None


class EvaluationResponse(BaseModel):
    success: bool
    assessment: Optional[AssessmentEventModel] = None
    error_message: Optional[str] = None
