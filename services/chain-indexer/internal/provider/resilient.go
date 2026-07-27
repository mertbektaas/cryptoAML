package provider

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"time"
)

// Resilient tries providers in order, retries transient failures with
// exponential backoff+jitter, and exposes the provider that succeeded.
// Circuit state is intentionally kept behind this boundary for the next
// increment; callers already receive a single fallback-safe interface.
type Resilient struct {
	Clients     []RPCClient
	MaxAttempts int
	BaseBackoff time.Duration
}

func (r Resilient) Call(ctx context.Context, method string, params any) (json.RawMessage, string, error) {
	if len(r.Clients) == 0 {
		return nil, "", fmt.Errorf("no rpc providers configured")
	}
	attempts := r.MaxAttempts
	if attempts < 1 {
		attempts = 3
	}
	base := r.BaseBackoff
	if base <= 0 {
		base = 250 * time.Millisecond
	}
	var last error
	for attempt := 0; attempt < attempts; attempt++ {
		for _, client := range r.Clients {
			data, err := client.Call(ctx, method, params)
			if err == nil {
				return data, client.Name, nil
			}
			last = err
		}
		backoff := base * time.Duration(1<<attempt)
		backoff += time.Duration(rand.Int63n(int64(base)))
		select {
		case <-ctx.Done():
			return nil, "", ctx.Err()
		case <-time.After(backoff):
		}
	}
	return nil, "", fmt.Errorf("all rpc providers failed: %w", last)
}
