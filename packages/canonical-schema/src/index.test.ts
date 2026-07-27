import assert from "node:assert";
import test from "node:test";
import {
  validateAddress,
  validateTransaction,
  validateToken,
  validateSmartContract,
  validateCrossChainBridge,
  CANONICAL_SCHEMA_VERSION
} from "./index.js";

test("validateAddress parses valid address data", () => {
  const validAddress = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    chain: "ETHEREUM",
    address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    entityType: "EXCHANGE",
    riskScore: 15,
    labels: ["binance", "hot-wallet"],
    metadata: { exchangeName: "Binance" },
    createdAt: "2026-07-27T10:00:00Z",
    updatedAt: "2026-07-27T10:00:00Z"
  };

  const parsed = validateAddress(validAddress);
  assert.strictEqual(parsed.chain, "ETHEREUM");
  assert.strictEqual(parsed.schemaVersion, CANONICAL_SCHEMA_VERSION);
});

test("validateTransaction parses valid transaction data", () => {
  const validTx = {
    id: "987e6543-e89b-12d3-a456-426614174000",
    txHash: "0xabc123",
    chain: "BITCOIN",
    blockNumber: 800000,
    timestamp: "2026-07-27T12:00:00Z",
    fromAddress: "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    toAddress: "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
    value: "5000000000",
    status: "SUCCESS"
  };

  const parsed = validateTransaction(validTx);
  assert.strictEqual(parsed.chain, "BITCOIN");
  assert.strictEqual(parsed.value, "5000000000");
  assert.strictEqual(parsed.schemaVersion, CANONICAL_SCHEMA_VERSION);
});
