package provider

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

type Caller interface {
	Call(context.Context, string, any) (json.RawMessage, string, error)
}

// CircuitBreaker prevents a persistently unhealthy provider group from being
// hammered. A successful probe closes the circuit again.
type CircuitBreaker struct {
	Underlying   Caller
	FailureLimit int
	OpenFor      time.Duration

	mu          sync.Mutex
	failures    int
	openedUntil time.Time
}

func (b *CircuitBreaker) Call(ctx context.Context, method string, params any) (json.RawMessage, string, error) {
	if b.Underlying == nil {
		return nil, "", fmt.Errorf("circuit breaker has no underlying caller")
	}
	limit := b.FailureLimit
	if limit < 1 {
		limit = 3
	}
	openFor := b.OpenFor
	if openFor <= 0 {
		openFor = 30 * time.Second
	}
	b.mu.Lock()
	if time.Now().Before(b.openedUntil) {
		until := b.openedUntil
		b.mu.Unlock()
		return nil, "", fmt.Errorf("rpc circuit open until %s", until.UTC().Format(time.RFC3339))
	}
	b.mu.Unlock()

	data, provider, err := b.Underlying.Call(ctx, method, params)
	b.mu.Lock()
	defer b.mu.Unlock()
	if err == nil {
		b.failures = 0
		b.openedUntil = time.Time{}
		return data, provider, nil
	}
	b.failures++
	if b.failures >= limit {
		b.openedUntil = time.Now().Add(openFor)
	}
	return nil, "", err
}
