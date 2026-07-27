package model

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"time"
)

// RawEnvelope is the provider-independent boundary consumed by F1-K2-A.
// Canonical Chain/Block/Transaction/Movement records are intentionally not
// produced here; the normalizer owns that transition.
type RawEnvelope struct {
	SchemaVersion  string          `json:"schema_version"`
	ChainNamespace string          `json:"chain_namespace"`
	BlockNumber    uint64          `json:"block_number"`
	BlockHash      string          `json:"block_hash,omitempty"`
	Provider       string          `json:"provider"`
	ObservedTime   time.Time       `json:"observed_time"`
	Method         string          `json:"method"`
	PayloadHash    string          `json:"payload_hash"`
	RawPayload     json.RawMessage `json:"raw_payload"`
}

func NewEnvelope(chain, provider, method string, block uint64, blockHash string, payload json.RawMessage) RawEnvelope {
	sum := sha256.Sum256(payload)
	return RawEnvelope{SchemaVersion: "1.0.0", ChainNamespace: chain, BlockNumber: block,
		BlockHash: blockHash, Provider: provider, ObservedTime: time.Now().UTC(),
		Method: method, PayloadHash: hex.EncodeToString(sum[:]), RawPayload: payload}
}
