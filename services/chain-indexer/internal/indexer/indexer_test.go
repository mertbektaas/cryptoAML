package indexer

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/mertbektaas/cryptoaml/chain-indexer/internal/model"
)

type fakeRPC struct{}

func (fakeRPC) Call(_ context.Context, method string, params any) (json.RawMessage, string, error) {
	switch method {
	case "eth_getBlockByNumber":
		return json.RawMessage(`{"hash":"0xblock","transactions":[{"hash":"0xtx"}]}`), "primary", nil
	case "eth_getTransactionReceipt":
		return json.RawMessage(`{"transactionHash":"0xtx","logs":[]}`), "primary", nil
	default:
		return nil, "", nil
	}
}

type memoryArchive struct{ values []model.RawEnvelope }

func (m *memoryArchive) Put(_ context.Context, _ string, e model.RawEnvelope) error {
	m.values = append(m.values, e)
	return nil
}

func TestRunRangeWritesHashedEnvelope(t *testing.T) {
	store := &memoryArchive{}
	err := (Indexer{ChainNamespace: "eip155:1", RPC: fakeRPC{}, Archive: store}).RunRange(context.Background(), 10, 10)
	if err != nil {
		t.Fatal(err)
	}
	if len(store.values) != 1 {
		t.Fatalf("got %d envelopes, want 1", len(store.values))
	}
	if store.values[0].PayloadHash == "" || store.values[0].SchemaVersion != "1.0.0" {
		t.Fatalf("invalid envelope: %+v", store.values[0])
	}
}
