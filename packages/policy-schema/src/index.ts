import { z } from "zod";

/**
 * Current version for policy and evidence schema
 */
export const POLICY_SCHEMA_VERSION = "1.0.0";

/**
 * Signal Severity Enum
 */
export const SeveritySchema = z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
export type Severity = z.infer<typeof SeveritySchema>;

/**
 * Signal Definition Schema
 */
export const SignalSchema = z.object({
  id: z.string().uuid("Signal ID must be a valid UUID"),
  code: z.string().min(1, "Signal code is required"),
  name: z.string().min(1, "Signal name is required"),
  category: z.enum(["SANCTIONS", "MIXER", "DARKNET", "RAPID_PASS_THROUGH", "HIGH_VOLUME", "NEW_CONTRACT", "CUSTOM"]),
  severity: SeveritySchema,
  observedValue: z.unknown(),
  metadata: z.record(z.string(), z.unknown()).default({}),
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type Signal = z.infer<typeof SignalSchema>;

/**
 * Rule Condition Operator Enum
 */
export const RuleOperatorSchema = z.enum(["EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN", "CONTAINS", "IN_LIST", "EXISTS"]);
export type RuleOperator = z.infer<typeof RuleOperatorSchema>;

/**
 * Weight Schema
 */
export const WeightSchema = z.object({
  ruleId: z.string().uuid("Rule ID must be a valid UUID"),
  weightValue: z.number().min(0).max(100),
  adjustmentReason: z.string().optional(),
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type Weight = z.infer<typeof WeightSchema>;

/**
 * Rule Definition Schema
 */
export const RuleSchema = z.object({
  id: z.string().uuid("Rule ID must be a valid UUID"),
  code: z.string().min(1, "Rule code is required"),
  name: z.string().min(1, "Rule name is required"),
  description: z.string().default(""),
  signalIds: z.array(z.string().uuid()).min(1, "At least one signal ID is required"),
  operator: RuleOperatorSchema,
  threshold: z.unknown(),
  weight: WeightSchema,
  isEnabled: z.boolean().default(true),
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type Rule = z.infer<typeof RuleSchema>;

/**
 * Cap / Floor Boundaries Schema
 */
export const CapFloorSchema = z.object({
  minScoreFloor: z.number().min(0).max(100).default(0),
  maxScoreCap: z.number().min(0).max(100).default(100),
  applySanctionOverrideCap: z.boolean().default(true), // Automatically caps at 100 if sanctioned
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type CapFloor = z.infer<typeof CapFloorSchema>;

/**
 * Risk Tier Definition Schema
 */
export const TierSchema = z.object({
  tierName: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  minScore: z.number().min(0).max(100),
  maxScore: z.number().min(0).max(100),
  actionRequired: z.enum(["NONE", "MONITOR", "REVIEW_REQUIRED", "BLOCK_IMMEDIATELY"]),
  description: z.string().optional(),
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type Tier = z.infer<typeof TierSchema>;

/**
 * Complete Risk Policy Schema
 */
export const PolicySchema = z.object({
  id: z.string().uuid("Policy ID must be a valid UUID"),
  name: z.string().min(1, "Policy name is required"),
  version: z.string().default(POLICY_SCHEMA_VERSION),
  description: z.string().default(""),
  rules: z.array(RuleSchema),
  capFloor: CapFloorSchema,
  tiers: z.array(TierSchema).min(1, "At least one tier definition is required"),
  isDefault: z.boolean().default(false),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});
export type Policy = z.infer<typeof PolicySchema>;

// ============================================================================
// F0-K2-B: EVIDENCE & EXPLAINABILITY MODEL SCHEMAS
// ============================================================================

/**
 * Source Type Enum for Evidence
 */
export const EvidenceSourceTypeSchema = z.enum([
  "ON_CHAIN_TX",
  "ON_CHAIN_EVENT",
  "SANCTION_LIST",
  "GRAPH_CLUSTER",
  "LABEL_REGISTRY",
  "EXTERNAL_INTEL"
]);
export type EvidenceSourceType = z.infer<typeof EvidenceSourceTypeSchema>;

/**
 * Evidence Reference Schema
 * Mandatory reference pointer back to raw transaction, log, sanction entry, or label
 */
export const EvidenceReferenceSchema = z.object({
  id: z.string().uuid("Evidence Reference ID must be a valid UUID"),
  sourceType: EvidenceSourceTypeSchema,
  referenceURI: z.string().min(1, "Reference URI is required (e.g. eip155:1/tx/0x...)"),
  chain: z.string().optional(),
  blockNumber: z.number().int().positive().optional(),
  observedAt: z.string().datetime(),
  metadata: z.record(z.string(), z.unknown()).default({})
});
export type EvidenceReference = z.infer<typeof EvidenceReferenceSchema>;

/**
 * Quality Metrics Schema
 * Mandatory fields for Coverage, Freshness, Finality, and Confidence
 */
export const QualityMetricsSchema = z.object({
  coverage: z.number().min(0).max(1).describe("Percentage of historical window covered (0.0 to 1.0)"),
  freshnessSeconds: z.number().nonnegative().describe("Age of evidence in seconds at evaluation time"),
  finality: z.enum(["UNCONFIRMED", "PROVISIONAL", "FINALIZED"]).describe("Block finality status"),
  confidence: z.number().min(0).max(1).describe("Certainty score of evidence or entity attribution (0.0 to 1.0)")
});
export type QualityMetrics = z.infer<typeof QualityMetricsSchema>;

/**
 * Explained Signal Schema
 * Maps Signal -> Evidence -> Contribution with required reasoning fields
 */
export const ExplainedSignalSchema = z.object({
  signalId: z.string().uuid("Signal ID must be a valid UUID"),
  signalCode: z.string().min(1, "Signal code is required"),
  reason: z.string().min(1, "Human-readable explanation is required"),
  observedValue: z.unknown(),
  operator: RuleOperatorSchema,
  expectedValue: z.unknown(),
  contribution: z.number().min(0).max(100).describe("Points contributed to overall risk score"),
  evidenceReferences: z.array(EvidenceReferenceSchema).min(1, "At least one evidence reference is mandatory"),
  qualityMetrics: QualityMetricsSchema
});
export type ExplainedSignal = z.infer<typeof ExplainedSignalSchema>;

/**
 * Reproducibility Metadata Schema
 * Complete provenance model: Dataset snapshot, feature version, policy version, and git commit SHA
 */
export const ReproducibilityMetadataSchema = z.object({
  datasetSnapshotId: z.string().min(1, "Dataset snapshot ID/hash is required"),
  featureVersion: z.string().min(1, "Feature pipeline version is required (e.g. v1.2.0)"),
  policyVersion: z.string().min(1, "Policy version is required (e.g. v1.0.0)"),
  modelVersion: z.string().min(1, "Model/Engine version is required (e.g. rule-engine-v1.0)"),
  codeCommitHash: z.string().min(7, "Git commit hash is required"),
  evaluatedAt: z.string().datetime()
});
export type ReproducibilityMetadata = z.infer<typeof ReproducibilityMetadataSchema>;

/**
 * Assessment Explainability Tree Schema
 * Full Evidence -> Signal -> Assessment chain model for auditability
 */
export const AssessmentExplainabilitySchema = z.object({
  assessmentId: z.string().uuid("Assessment ID must be a valid UUID"),
  targetAddress: z.string().min(1, "Target address is required"),
  finalRiskScore: z.number().min(0).max(100),
  riskTier: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  explainedSignals: z.array(ExplainedSignalSchema),
  reproducibilityMetadata: ReproducibilityMetadataSchema,
  overallConfidence: z.number().min(0).max(1),
  schemaVersion: z.string().default(POLICY_SCHEMA_VERSION)
});
export type AssessmentExplainability = z.infer<typeof AssessmentExplainabilitySchema>;

// ============================================================================
// VALIDATION HELPER FUNCTIONS
// ============================================================================

export function validateSignal(data: unknown): Signal {
  return SignalSchema.parse(data);
}

export function validateRule(data: unknown): Rule {
  return RuleSchema.parse(data);
}

export function validatePolicy(data: unknown): Policy {
  return PolicySchema.parse(data);
}

export function validateTier(data: unknown): Tier {
  return TierSchema.parse(data);
}

export function validateEvidenceReference(data: unknown): EvidenceReference {
  return EvidenceReferenceSchema.parse(data);
}

export function validateExplainedSignal(data: unknown): ExplainedSignal {
  return ExplainedSignalSchema.parse(data);
}

export function validateReproducibilityMetadata(data: unknown): ReproducibilityMetadata {
  return ReproducibilityMetadataSchema.parse(data);
}

export function validateAssessmentExplainability(data: unknown): AssessmentExplainability {
  return AssessmentExplainabilitySchema.parse(data);
}
