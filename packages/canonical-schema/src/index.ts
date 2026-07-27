import { z } from "zod";

/**
 * Current version for canonical schemas
 */
export const CANONICAL_SCHEMA_VERSION = "1.0.0";

/**
 * Blockchain network enum
 */
export const ChainNetworkSchema = z.enum([
  "BITCOIN",
  "ETHEREUM",
  "POLYGON",
  "ARBITRUM",
  "OPTIMISM",
  "AVALANCHE",
  "SOLANA",
  "BSC",
  "TRON"
]);
export type ChainNetwork = z.infer<typeof ChainNetworkSchema>;

/**
 * Address Entity Schema
 */
export const AddressSchema = z.object({
  id: z.string().uuid("Address ID must be a valid UUID"),
  chain: ChainNetworkSchema,
  address: z.string().min(1, "Address cannot be empty"),
  entityType: z.enum(["INDIVIDUAL", "EXCHANGE", "MIXER", "SMART_CONTRACT", "MINER", "UNKNOWN"]),
  riskScore: z.number().min(0).max(100).default(0),
  labels: z.array(z.string()).default([]),
  metadata: z.record(z.string(), z.unknown()).default({}),
  schemaVersion: z.string().default(CANONICAL_SCHEMA_VERSION),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime()
});
export type Address = z.infer<typeof AddressSchema>;

/**
 * Token Standard Enum
 */
export const TokenTypeSchema = z.enum(["NATIVE", "ERC20", "ERC721", "ERC1155", "SPL"]);
export type TokenType = z.infer<typeof TokenTypeSchema>;

/**
 * Token Entity Schema
 */
export const TokenSchema = z.object({
  id: z.string().uuid("Token ID must be a valid UUID"),
  chain: ChainNetworkSchema,
  contractAddress: z.string().nullable(),
  symbol: z.string().min(1, "Token symbol is required"),
  name: z.string().min(1, "Token name is required"),
  decimals: z.number().int().min(0).max(36).default(18),
  tokenType: TokenTypeSchema,
  schemaVersion: z.string().default(CANONICAL_SCHEMA_VERSION),
  createdAt: z.string().datetime()
});
export type Token = z.infer<typeof TokenSchema>;

/**
 * Token Transfer Details Schema
 */
export const TokenTransferSchema = z.object({
  tokenAddress: z.string(),
  fromAddress: z.string(),
  toAddress: z.string(),
  amount: z.string(), // String to handle large numbers safely
  decimalAmount: z.number()
});
export type TokenTransfer = z.infer<typeof TokenTransferSchema>;

/**
 * Transaction Entity Schema
 */
export const TransactionSchema = z.object({
  id: z.string().uuid("Transaction ID must be a valid UUID"),
  txHash: z.string().min(1, "Transaction hash is required"),
  chain: ChainNetworkSchema,
  blockNumber: z.number().int().positive(),
  timestamp: z.string().datetime(),
  fromAddress: z.string().min(1, "From address is required"),
  toAddress: z.string().nullable(),
  value: z.string(), // Native value as string (wei/satoshi)
  fee: z.string().default("0"),
  status: z.enum(["SUCCESS", "FAILED", "PENDING"]),
  tokenTransfers: z.array(TokenTransferSchema).default([]),
  inputData: z.string().default("0x"),
  schemaVersion: z.string().default(CANONICAL_SCHEMA_VERSION)
});
export type Transaction = z.infer<typeof TransactionSchema>;

/**
 * Smart Contract Entity Schema
 */
export const SmartContractSchema = z.object({
  id: z.string().uuid("Smart Contract ID must be a valid UUID"),
  chain: ChainNetworkSchema,
  address: z.string().min(1, "Contract address is required"),
  creatorAddress: z.string().min(1, "Creator address is required"),
  creationTxHash: z.string().min(1, "Creation transaction hash is required"),
  isVerified: z.boolean().default(false),
  contractType: z.enum(["TOKEN", "DEX", "BRIDGE", "LENDING", "GOVERNANCE", "OTHER"]),
  bytecodeHash: z.string().optional(),
  schemaVersion: z.string().default(CANONICAL_SCHEMA_VERSION),
  createdAt: z.string().datetime()
});
export type SmartContract = z.infer<typeof SmartContractSchema>;

/**
 * Cross-Chain Bridge Entity Schema
 */
export const CrossChainBridgeSchema = z.object({
  id: z.string().uuid("Bridge ID must be a valid UUID"),
  sourceChain: ChainNetworkSchema,
  targetChain: ChainNetworkSchema,
  bridgeName: z.string().min(1, "Bridge name is required"),
  contractAddresses: z.record(ChainNetworkSchema, z.string()),
  supportedTokens: z.array(z.string()).default([]),
  schemaVersion: z.string().default(CANONICAL_SCHEMA_VERSION),
  createdAt: z.string().datetime()
});
export type CrossChainBridge = z.infer<typeof CrossChainBridgeSchema>;

/**
 * Validation Helper Functions
 */
export function validateAddress(data: unknown): Address {
  return AddressSchema.parse(data);
}

export function validateTransaction(data: unknown): Transaction {
  return TransactionSchema.parse(data);
}

export function validateToken(data: unknown): Token {
  return TokenSchema.parse(data);
}

export function validateSmartContract(data: unknown): SmartContract {
  return SmartContractSchema.parse(data);
}

export function validateCrossChainBridge(data: unknown): CrossChainBridge {
  return CrossChainBridgeSchema.parse(data);
}
