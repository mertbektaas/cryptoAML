import assert from "node:assert";
import test from "node:test";
import {
  validateRawIngestedEvent,
  validateNormalizedMovementEvent,
  validateAssessmentEvent,
  EVENT_CONTRACTS_VERSION
} from "./index.js";

test("validateNormalizedMovementEvent parses token transfer event", () => {
  const validEvent = {
    eventId: "11111111-2222-3333-4444-555555555555",
    eventType: "TOKEN_MOVEMENT",
    chain: "ETHEREUM",
    transactionHash: "0x1234567890abcdef",
    blockNumber: 19000000,
    fromAddress: "0xSenderAddress",
    toAddress: "0xReceiverAddress",
    tokenAddress: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    tokenSymbol: "USDT",
    rawAmount: "1000000000",
    decimalAmount: 1000,
    usdValueAtTimestamp: 1000,
    timestamp: "2026-07-27T13:00:00Z"
  };

  const parsed = validateNormalizedMovementEvent(validEvent);
  assert.strictEqual(parsed.eventType, "TOKEN_MOVEMENT");
  assert.strictEqual(parsed.contractVersion, EVENT_CONTRACTS_VERSION);
  assert.strictEqual(parsed.decimalAmount, 1000);
});

test("validateAssessmentEvent parses risk assessment event", () => {
  const validAssessment = {
    eventId: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    eventType: "RISK_ASSESSMENT",
    targetAddress: "0xSuspiciousAddress",
    chain: "ETHEREUM",
    finalRiskScore: 85,
    riskTier: "HIGH",
    matchedSignals: [
      {
        signalId: "SIG-001",
        signalCode: "MIXER_EXPOSURE",
        severity: "HIGH",
        observedValue: true,
        weightContribution: 45
      }
    ],
    policyId: "99999999-8888-7777-6666-555555555555",
    evaluatedAt: "2026-07-27T13:05:00Z"
  };

  const parsed = validateAssessmentEvent(validAssessment);
  assert.strictEqual(parsed.riskTier, "HIGH");
  assert.strictEqual(parsed.finalRiskScore, 85);
  assert.strictEqual(parsed.contractVersion, EVENT_CONTRACTS_VERSION);
});
