import { z } from "zod";

/**
 * Current version for event contract schemas
 */
export const EVENT_CONTRACTS_VERSION = "1.0.0";

/**
 * Raw Ingested Event Schema (Data ingested directly from node/indexer)
 */
export const RawIngestedEventSchema = z.object({
  eventId: z.string().uuid("Event ID must be a valid UUID"),
  eventType: z.enum(["RAW_BLOCK", "RAW_TRANSACTION", "RAW_LOG"]),
  chain: z.string().min(1, "Chain is required"),
  timestamp: z.string().datetime(),
  rawData: z.record(z.string(), z.unknown()),
  correlationId: z.string().uuid().optional(),
  contractVersion: z.string().default(EVENT_CONTRACTS_VERSION)
});
export type RawIngestedEvent = z.infer<typeof RawIngestedEventSchema>;

/**
 * Normalized Movement Event Schema (Standardized token/native transfer event)
 */
export const NormalizedMovementEventSchema = z.object({
  eventId: z.string().uuid("Event ID must be a valid UUID"),
  eventType: z.literal("TOKEN_MOVEMENT"),
  chain: z.string().min(1, "Chain is required"),
  transactionHash: z.string().min(1, "Transaction hash is required"),
  blockNumber: z.number().int().positive(),
  fromAddress: z.string().min(1, "From address is required"),
  toAddress: z.string().min(1, "To address is required"),
  tokenAddress: z.string().nullable().default(null), // null for native currency
  tokenSymbol: z.string().default("ETH"),
  rawAmount: z.string(), // Wei/Satoshi string representation
  decimalAmount: z.number(),
  usdValueAtTimestamp: z.number().nullable().optional(),
  timestamp: z.string().datetime(),
  correlationId: z.string().uuid().optional(),
  contractVersion: z.string().default(EVENT_CONTRACTS_VERSION)
});
export type NormalizedMovementEvent = z.infer<typeof NormalizedMovementEventSchema>;

/**
 * Matched Signal Summary Schema
 */
export const MatchedSignalSummarySchema = z.object({
  signalId: z.string(),
  signalCode: z.string(),
  severity: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  observedValue: z.unknown(),
  weightContribution: z.number()
});
export type MatchedSignalSummary = z.infer<typeof MatchedSignalSummarySchema>;

/**
 * Assessment Event Schema (Risk evaluation result event)
 */
export const AssessmentEventSchema = z.object({
  eventId: z.string().uuid("Event ID must be a valid UUID"),
  eventType: z.literal("RISK_ASSESSMENT"),
  targetAddress: z.string().min(1, "Target address is required"),
  chain: z.string().min(1, "Chain is required"),
  finalRiskScore: z.number().min(0).max(100),
  riskTier: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  matchedSignals: z.array(MatchedSignalSummarySchema).default([]),
  policyId: z.string().uuid("Policy ID must be a valid UUID"),
  evaluatedAt: z.string().datetime(),
  correlationId: z.string().uuid().optional(),
  contractVersion: z.string().default(EVENT_CONTRACTS_VERSION)
});
export type AssessmentEvent = z.infer<typeof AssessmentEventSchema>;

/**
 * Validation Helper Functions
 */
export function validateRawIngestedEvent(data: unknown): RawIngestedEvent {
  return RawIngestedEventSchema.parse(data);
}

export function validateNormalizedMovementEvent(data: unknown): NormalizedMovementEvent {
  return NormalizedMovementEventSchema.parse(data);
}

export function validateAssessmentEvent(data: unknown): AssessmentEvent {
  return AssessmentEventSchema.parse(data);
}
