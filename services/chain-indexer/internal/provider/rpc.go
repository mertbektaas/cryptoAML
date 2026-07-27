package provider

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type RPCClient struct {
	Name       string
	URL        string
	HTTPClient *http.Client
}

type rpcRequest struct {
	JSONRPC string `json:"jsonrpc"`
	ID      int    `json:"id"`
	Method  string `json:"method"`
	Params  any    `json:"params"`
}
type rpcResponse struct {
	Result json.RawMessage `json:"result"`
	Error  *struct {
		Code    int    `json:"code"`
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

func (c RPCClient) Call(ctx context.Context, method string, params any) (json.RawMessage, error) {
	body, err := json.Marshal(rpcRequest{JSONRPC: "2.0", ID: 1, Method: method, Params: params})
	if err != nil {
		return nil, fmt.Errorf("marshal rpc request: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.URL, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("create rpc request: %w", err)
	}
	req.Header.Set("content-type", "application/json")
	hc := c.HTTPClient
	if hc == nil {
		hc = &http.Client{Timeout: 15 * time.Second}
	}
	resp, err := hc.Do(req)
	if err != nil {
		return nil, fmt.Errorf("provider %s request: %w", c.Name, err)
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 64<<20))
	if err != nil {
		return nil, fmt.Errorf("read rpc response: %w", err)
	}
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("provider %s http status %d", c.Name, resp.StatusCode)
	}
	var decoded rpcResponse
	if err := json.Unmarshal(data, &decoded); err != nil {
		return nil, fmt.Errorf("decode rpc response: %w", err)
	}
	if decoded.Error != nil {
		return nil, fmt.Errorf("provider %s rpc %d: %s", c.Name, decoded.Error.Code, decoded.Error.Message)
	}
	return decoded.Result, nil
}
