package indexer

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/mertbektaas/cryptoaml/chain-indexer/internal/archive"
	"github.com/mertbektaas/cryptoaml/chain-indexer/internal/model"
)

type Caller interface {
	Call(context.Context, string, any) (json.RawMessage, string, error)
}

type Indexer struct {
	ChainNamespace string
	RPC            Caller
	Archive        archive.Writer
	PollInterval   time.Duration
}

type blockPayload struct {
	Block    json.RawMessage   `json:"block"`
	Receipts []json.RawMessage `json:"receipts"`
}

func (i Indexer) RunRange(ctx context.Context, start, end uint64) error {
	if end < start {
		return fmt.Errorf("end block %d is before start block %d", end, start)
	}
	if i.RPC == nil || i.Archive == nil {
		return fmt.Errorf("rpc and archive are required")
	}
	for n := start; n <= end; n++ {
		if err := i.indexBlock(ctx, n); err != nil {
			return err
		}
		if n == ^uint64(0) {
			break
		}
	}
	return nil
}

func (i Indexer) RunLive(ctx context.Context, from uint64) error {
	interval := i.PollInterval
	if interval <= 0 {
		interval = 5 * time.Second
	}
	next := from
	for {
		latestRaw, _, err := i.RPC.Call(ctx, "eth_blockNumber", []any{})
		if err != nil {
			return err
		}
		latest, err := parseHexUint(latestRaw)
		if err != nil {
			return fmt.Errorf("decode latest block: %w", err)
		}
		if latest >= next {
			if err := i.RunRange(ctx, next, latest); err != nil {
				return err
			}
			next = latest + 1
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(interval):
		}
	}
}

func (i Indexer) indexBlock(ctx context.Context, number uint64) error {
	blockRaw, provider, err := i.RPC.Call(ctx, "eth_getBlockByNumber", []any{fmt.Sprintf("0x%x", number), true})
	if err != nil {
		return fmt.Errorf("get block %d: %w", number, err)
	}
	var block struct {
		Hash         string `json:"hash"`
		Transactions []struct {
			Hash string `json:"hash"`
		} `json:"transactions"`
	}
	if err := json.Unmarshal(blockRaw, &block); err != nil {
		return fmt.Errorf("decode block %d: %w", number, err)
	}
	receipts := make([]json.RawMessage, 0, len(block.Transactions))
	for _, tx := range block.Transactions {
		receipt, receiptProvider, err := i.RPC.Call(ctx, "eth_getTransactionReceipt", []any{tx.Hash})
		if err != nil {
			return fmt.Errorf("get receipt %s: %w", tx.Hash, err)
		}
		if receiptProvider != provider {
			provider = provider + "," + receiptProvider
		}
		receipts = append(receipts, receipt)
	}
	payload, err := json.Marshal(blockPayload{Block: blockRaw, Receipts: receipts})
	if err != nil {
		return err
	}
	envelope := model.NewEnvelope(i.ChainNamespace, provider, "eth_getBlockByNumber", number, block.Hash, payload)
	key := fmt.Sprintf("raw/%s/blocks/%012d.json.gz", strings.ReplaceAll(i.ChainNamespace, ":", "-"), number)
	return i.Archive.Put(ctx, key, envelope)
}

func parseHexUint(raw json.RawMessage) (uint64, error) {
	var value string
	if err := json.Unmarshal(raw, &value); err != nil {
		return 0, err
	}
	value = strings.TrimPrefix(value, "0x")
	if value == "" {
		return 0, nil
	}
	return strconv.ParseUint(value, 16, 64)
}

func BlockTag(number uint64) string {
	var b [8]byte
	for n := 7; n >= 0; n-- {
		b[n] = byte(number)
		number >>= 8
	}
	return "0x" + hex.EncodeToString(bytesTrimLeftZero(b[:]))
}
func bytesTrimLeftZero(value []byte) []byte {
	trimmed := strings.TrimLeft(string(value), "\x00")
	if trimmed == "" {
		return []byte{0}
	}
	return []byte(trimmed)
}
