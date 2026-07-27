import assert from "node:assert";
import test from "node:test";
import {
  validateSignal,
  validateRule,
  validatePolicy,
  validateEvidenceReference,
  validateExplainedSignal,
  validateReproducibilityMetadata,
  validateAssessmentExplainability,
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

// ============================================================================
// F0-K2-B EVIDENCE & EXPLAINABILITY UNIT TESTS
// ============================================================================

test("validateEvidenceReference parses valid on-chain evidence reference", () => {
  const evidence = {
    id: "e1e2e3e4-e5e6-7e8e-9e0e-1e2e3e4e5e6e",
    sourceType: "ON_CHAIN_TX",
    referenceURI: "eip155:1/tx/0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    chain: "ETHEREUM",
    blockNumber: 19500000,
    observedAt: "2026-07-27T15:00:00Z"
  };

  const parsed = validateEvidenceReference(evidence);
  assert.strictEqual(parsed.sourceType, "ON_CHAIN_TX");
  assert.strictEqual(parsed.blockNumber, 19500000);
});

test("validateExplainedSignal parses signal with reason, contribution and quality metrics", () => {
  const evidenceId = "e1e2e3e4-e5e6-7e8e-9e0e-1e2e3e4e5e6e";
  const signalId = "22222222-2222-2222-2222-222222222222";

  const explainedSignal = {
    signalId: signalId,
    signalCode: "MIXER_INTERACTION",
    reason: "Direct interaction with Tornado Cash mixer smart contract within last 24 hours",
    observedValue: "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    operator: "EQUALS",
    expectedValue: "KNOWN_MIXER_ADDRESS",
    contribution: 50,
    evidenceReferences: [
      {
        id: evidenceId,
        sourceType: "ON_CHAIN_TX",
        referenceURI: "eip155:1/tx/0x9999",
        observedAt: "2026-07-27T15:10:00Z"
      }
    ],
    qualityMetrics: {
      coverage: 1.0,
      freshnessSeconds: 120,
      finality: "FINALIZED",
      confidence: 0.98
    }
  };

  const parsed = validateExplainedSignal(explainedSignal);
  assert.strictEqual(parsed.signalCode, "MIXER_INTERACTION");
  assert.strictEqual(parsed.contribution, 50);
  assert.strictEqual(parsed.qualityMetrics.finality, "FINALIZED");
});

test("validateAssessmentExplainability parses full Evidence -> Signal -> Assessment chain", () => {
  const assessment = {
    assessmentId: "a0a0a0a0-b1b1-c2c2-d3d3-e4e4e4e4e4e4",
    targetAddress: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    finalRiskScore: 85,
    riskTier: "HIGH",
    explainedSignals: [
      {
        signalId: "22222222-2222-2222-2222-222222222222",
        signalCode: "MIXER_INTERACTION",
        reason: "Direct mixer interaction detected",
        observedValue: true,
        operator: "EQUALS",
        expectedValue: true,
        contribution: 50,
        evidenceReferences: [
          {
            id: "e1e2e3e4-e5e6-7e8e-9e0e-1e2e3e4e5e6e",
            sourceType: "ON_CHAIN_TX",
            referenceURI: "eip155:1/tx/0x9999",
            observedAt: "2026-07-27T15:10:00Z"
          }
        ],
        qualityMetrics: {
          coverage: 1.0,
          freshnessSeconds: 60,
          finality: "FINALIZED",
          confidence: 0.99
        }
      }
    ],
    reproducibilityMetadata: {
      datasetSnapshotId: "snapshot-20260727-001",
      featureVersion: "v1.2.0",
      policyVersion: "v1.0.0",
      modelVersion: "rule-engine-v1.0",
      codeCommitHash: "71a4dd07ef6fba89d06c828632849f8f5e745553",
      evaluatedAt: "2026-07-27T15:20:00Z"
    },
    overallConfidence: 0.98,
    schemaVersion: POLICY_SCHEMA_VERSION
  };

  const parsed = validateAssessmentExplainability(assessment);
  assert.strictEqual(parsed.finalRiskScore, 85);
  assert.strictEqual(parsed.riskTier, "HIGH");
  assert.strictEqual(parsed.reproducibilityMetadata.codeCommitHash, "71a4dd07ef6fba89d06c828632849f8f5e745553");
});
