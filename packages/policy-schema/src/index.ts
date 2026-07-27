import { z } from "zod";

/**
 * Current version for policy schema
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

/**
 * Validation Helper Functions
 */
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
