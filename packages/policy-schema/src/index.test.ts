import assert from "node:assert";
import test from "node:test";
import {
  validateSignal,
  validateRule,
  validatePolicy,
  POLICY_SCHEMA_VERSION
} from "./index.js";

test("validateSignal parses valid signal data", () => {
  const validSignal = {
    id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    code: "SANCTION_MATCH",
    name: "Sanctioned Entity Direct Interaction",
    category: "SANCTIONS",
    severity: "CRITICAL",
    observedValue: { listName: "OFAC", entryId: "12345" }
  };

  const parsed = validateSignal(validSignal);
  assert.strictEqual(parsed.category, "SANCTIONS");
  assert.strictEqual(parsed.severity, "CRITICAL");
  assert.strictEqual(parsed.schemaVersion, POLICY_SCHEMA_VERSION);
});

test("validatePolicy parses complete policy configuration", () => {
  const ruleId = "11111111-1111-1111-1111-111111111111";
  const signalId = "22222222-2222-2222-2222-222222222222";

  const validPolicy = {
    id: "33333333-3333-3333-3333-333333333333",
    name: "Default Enterprise Risk Policy",
    version: POLICY_SCHEMA_VERSION,
    description: "Standard risk scoring policy for production",
    rules: [
      {
        id: ruleId,
        code: "RULE_SANCTION_BLOCK",
        name: "Block Sanctioned Interactions",
        signalIds: [signalId],
        operator: "EQUALS",
        threshold: true,
        weight: {
          ruleId: ruleId,
          weightValue: 100,
          adjustmentReason: "Sanctioned entities carry max score"
        },
        isEnabled: true
      }
    ],
    capFloor: {
      minScoreFloor: 0,
      maxScoreCap: 100,
      applySanctionOverrideCap: true
    },
    tiers: [
      {
        tierName: "LOW",
        minScore: 0,
        maxScore: 29,
        actionRequired: "NONE"
      },
      {
        tierName: "MEDIUM",
        minScore: 30,
        maxScore: 69,
        actionRequired: "MONITOR"
      },
      {
        tierName: "HIGH",
        minScore: 70,
        maxScore: 89,
        actionRequired: "REVIEW_REQUIRED"
      },
      {
        tierName: "CRITICAL",
        minScore: 90,
        maxScore: 100,
        actionRequired: "BLOCK_IMMEDIATELY"
      }
    ],
    isDefault: true,
    createdAt: "2026-07-27T14:00:00Z",
    updatedAt: "2026-07-27T14:00:00Z"
  };

  const parsed = validatePolicy(validPolicy);
  assert.strictEqual(parsed.name, "Default Enterprise Risk Policy");
  assert.strictEqual(parsed.tiers.length, 4);
  assert.strictEqual(parsed.rules[0].weight.weightValue, 100);
});
