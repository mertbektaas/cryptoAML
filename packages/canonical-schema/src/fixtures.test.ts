import assert from "node:assert";
import test from "node:test";
import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";
import { validateTransaction, validateSmartContract } from "./index.js";

const rootDir = path.resolve(process.cwd(), "../../");

test("raw-transactions.yaml fixtures validate correctly against schemas", () => {
  const yamlPath = path.join(rootDir, "tests/fixtures/raw-transactions.yaml");
  assert.strictEqual(fs.existsSync(yamlPath), true, "raw-transactions.yaml must exist");

  const fileContent = fs.readFileSync(yamlPath, "utf-8");
  const doc = parseYaml(fileContent);

  assert.strictEqual(doc.version, "1.0.0");
  assert.strictEqual(doc.license, "MIT");
  assert.ok(doc.fixtures, "fixtures object must exist");

  // Validate Native Transfer Fixture
  const nativeTx = doc.fixtures.native_transfer;
  const validatedNative = validateTransaction(nativeTx);
  assert.strictEqual(validatedNative.chain, "ETHEREUM");
  assert.strictEqual(validatedNative.value, "1000000000000000000");

  // Validate ERC-20 Transfer Fixture
  const erc20Tx = doc.fixtures.erc20_transfer;
  const validatedErc20 = validateTransaction(erc20Tx);
  assert.strictEqual(validatedErc20.chain, "ETHEREUM");
  assert.strictEqual(validatedErc20.toAddress, "0x0000000000000000000000000000000000000002");

  // Validate Contract Creation Fixture
  const contractCreation = doc.fixtures.contract_creation;
  assert.strictEqual(contractCreation.createdContractAddress, "0x5555555555555555555555555555555555555555");
});

test("golden-datasets YAML files exist and have valid structure", () => {
  const normalizedPath = path.join(rootDir, "tests/golden-datasets/normalized-movements.yaml");
  const graphPath = path.join(rootDir, "tests/golden-datasets/graph-topologies.yaml");

  assert.strictEqual(fs.existsSync(normalizedPath), true, "normalized-movements.yaml must exist");
  assert.strictEqual(fs.existsSync(graphPath), true, "graph-topologies.yaml must exist");

  const normalizedDoc = parseYaml(fs.readFileSync(normalizedPath, "utf-8"));
  assert.ok(normalizedDoc.golden_outputs.native_transfer_golden);
  assert.ok(normalizedDoc.golden_outputs.erc20_transfer_golden);

  const graphDoc = parseYaml(fs.readFileSync(graphPath, "utf-8"));
  assert.ok(graphDoc.topologies.rapid_pass_through);
  assert.ok(graphDoc.topologies.fan_in);
  assert.ok(graphDoc.topologies.fan_out);
  assert.ok(graphDoc.topologies.label_exposure);
});
