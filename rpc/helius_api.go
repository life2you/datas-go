package rpc

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/life2you/datas-go/models/req"
	"github.com/life2you/datas-go/models/resp"

	"encoding/base64"

	"github.com/life2you/datas-go/configs"
	"github.com/life2you/datas-go/logger"
	"go.uber.org/zap"
)

// HeliusClient 表示 Helius HTTP API 客户端
type HeliusApiClient struct {
	httpClient *http.Client
	endpoint   string
	apiKey     string
	proxyURL   string
}

var GlobalHeliusClient *HeliusApiClient

// NewHeliusClientFromConfig 从配置创建一个新的 Helius HTTP API 客户端
func NewHeliusClient(config *configs.HeliusAPIConfig) *HeliusApiClient {
	// 使用与 WebSocket 相同的网络类型和 API 密钥
	baseURL := config.Endpoint
	apiKey := config.APIKey

	// 创建一个带有超时设置的 HTTP 客户端
	httpClient := &http.Client{
		Timeout: 120 * time.Second,
	}

	// 如果配置了代理，设置代理
	if config.ProxyURL != "" {
		proxyURL, err := url.Parse(config.ProxyURL)
		if err != nil {
			logger.Error("解析代理URL失败", zap.Error(err))
		} else {
			httpClient.Transport = &http.Transport{
				Proxy: http.ProxyURL(proxyURL),
			}
			logger.Info("Helius HTTP API 客户端将使用代理", zap.String("proxy", config.ProxyURL))
		}
	}

	client := &HeliusApiClient{
		httpClient: httpClient,
		endpoint:   baseURL,
		apiKey:     apiKey,
		proxyURL:   config.ProxyURL,
	}

	GlobalHeliusClient = client
	logger.Info("Helius HTTP API 客户端初始化完成", zap.String("endpoint", baseURL))

	return client
}

// SetProxyURL 设置代理URL
func (c *HeliusApiClient) SetProxyURL(proxyURLStr string) error {
	if proxyURLStr == "" {
		return nil
	}

	proxyURL, err := url.Parse(proxyURLStr)
	if err != nil {
		return fmt.Errorf("解析代理URL失败: %w", err)
	}

	c.proxyURL = proxyURLStr
	c.httpClient.Transport = &http.Transport{
		Proxy: http.ProxyURL(proxyURL),
	}

	return nil
}

// 发送 HTTP 请求到 Helius API
func (c *HeliusApiClient) makeRequest(ctx context.Context, method string, params []interface{}) (json.RawMessage, error) {
	// 构建请求 URL（添加 API 密钥）
	requestURL := fmt.Sprintf("%s/?api-key=%s", c.endpoint, c.apiKey)

	// 构建请求体
	requestBody := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  method,
		"params":  params,
	}

	// 将请求体序列化为 JSON
	requestJSON, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 创建 HTTP 请求
	req, err := http.NewRequestWithContext(ctx, "POST", requestURL, bytes.NewBuffer(requestJSON))
	if err != nil {
		return nil, fmt.Errorf("创建HTTP请求失败: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	// 发送请求
	respJson, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送HTTP请求失败: %w", err)
	}
	defer respJson.Body.Close()

	// 读取响应体
	respBody, err := io.ReadAll(respJson.Body)
	if err != nil {
		return nil, fmt.Errorf("读取响应失败: %w", err)
	}

	// 解析响应
	var response resp.HeliusResponse
	if err := json.Unmarshal(respBody, &response); err != nil {
		return nil, fmt.Errorf("解析响应失败: %w", err)
	}

	// 检查错误
	if response.Error != nil {
		return nil, fmt.Errorf("API返回错误: 代码=%d, 消息=%s", response.Error.Code, response.Error.Message)
	}

	return response.Result, nil
}

// GetBlock 获取指定槽位的区块数据
func (c *HeliusApiClient) GetBlock(ctx context.Context, slot uint64, params *req.GetBlockParams) (json.RawMessage, error) {
	//如果没有提供参数，使用默认参数
	if params == nil {
		// 默认不包含奖励信息，减少响应大小
		params = &req.GetBlockParams{
			Encoding:                       "json",
			TransactionDetails:             "full",
			MaxSupportedTransactionVersion: 0,
			Commitment:                     "finalized",
		}
	}

	// 构建请求参数
	requestParams := []interface{}{slot, params}

	// 发送请求
	logger.Debug("请求区块数据", zap.Uint64("slot", slot))
	result, err := c.makeRequest(ctx, "getBlock", requestParams)
	if err != nil {
		return nil, fmt.Errorf("获取区块数据失败 (slot=%d): %w", slot, err)
	}

	logger.Debug("成功获取区块数据", zap.Uint64("slot", slot))
	return result, nil
}

type HeliusEnhancedApiClient struct {
	apiKey     string
	httpClient *http.Client
	endpoint   string
	proxyURL   string
}

// 全局增强API客户端池
var GlobalHeliusEnhancedApiClients []*HeliusEnhancedApiClient

// ParseTransactionsRequest 表示解析交易请求的参数
type ParseTransactionsRequest struct {
	Transactions []string `json:"transactions"` // 交易签名数组
}

// ParseTransactionsResponse 表示解析交易响应的结构
type ParseTransactionsResponse struct {
	EnrichedTransactions []json.RawMessage `json:"enriched_transactions"`
}

// NewHeliusEnhancedApiClient 创建一个新的Helius Enhanced API客户端池
func NewHeliusEnhancedApiClient(config *configs.HeliusEnhancedAPIConfig) {
	httpClient := &http.Client{
		Timeout: 120 * time.Second,
	}
	// 处理多个API key
	if len(config.APIKeys) > 0 {
		for i, apiKey := range config.APIKeys {
			client := &HeliusEnhancedApiClient{
				apiKey:     apiKey,
				httpClient: httpClient,
				endpoint:   config.Endpoint,
				proxyURL:   config.ProxyURL,
			}
			GlobalHeliusEnhancedApiClients = append(GlobalHeliusEnhancedApiClients, client)
			logger.Info("创建Helius增强API客户端", zap.Int("索引", i), zap.String("endpoint", config.Endpoint))
		}
	}

	logger.Info("Helius增强API客户端池初始化完成", zap.Int("客户端数量", len(GlobalHeliusEnhancedApiClients)))
}

// GetClientCount 获取客户端数量
func GetEnhancedApiClientCount() int {
	return len(GlobalHeliusEnhancedApiClients)
}

// GetClientByIndex 根据索引获取客户端
func GetEnhancedApiClientByIndex(index int) *HeliusEnhancedApiClient {
	return GlobalHeliusEnhancedApiClients[index]
}

// ParseTransactions 解析一个或多个交易并返回人类可读的结构化数据
// 参数:
//   - ctx: 上下文
//   - signatures: 一个或多个交易签名
//
// 返回:
//   - []ParsedTransaction: 解析后的交易数据
//   - error: 错误信息
func (c *HeliusEnhancedApiClient) ParseTransactions(ctx context.Context, signatures ...string) ([]byte, error) {
	if len(signatures) == 0 {
		return nil, fmt.Errorf("至少需要提供一个交易签名")
	}

	// 构建 Enhanced Transactions API 的 URL
	apiURL := fmt.Sprintf("%s/v0/transactions?api-key=%s", c.endpoint, c.apiKey)

	// 构建请求体
	requestBody := ParseTransactionsRequest{
		Transactions: signatures,
	}

	// 将请求体序列化为 JSON
	requestJSON, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 使用 Authorization 头发送请求
	respBody, err := c.makeRequestWithAuth(ctx, "POST", apiURL, requestJSON)
	if err != nil {
		return nil, fmt.Errorf("解析交易失败: %w", err)
	}

	return respBody, nil
}

// 添加 Authorization 支持
func (c *HeliusEnhancedApiClient) makeRequestWithAuth(ctx context.Context, method string, endpoint string, requestJSON []byte) ([]byte, error) {
	// 创建 HTTP 请求
	req, err := http.NewRequestWithContext(ctx, method, endpoint, bytes.NewBuffer(requestJSON))
	if err != nil {
		return nil, fmt.Errorf("创建 HTTP 请求失败: %w", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")

	// 如果设置了 API 密钥，添加 Authorization 头
	if c.apiKey != "" {
		// 创建 Basic Auth 字符串 (username:password)
		// 在 Helius API 中，用户名是 API 密钥，密码可以为空
		auth := base64.StdEncoding.EncodeToString([]byte(c.apiKey + ":"))
		req.Header.Set("Authorization", "Basic "+auth)
	}

	// 发送请求
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("发送 HTTP 请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应体
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取响应失败: %w", err)
	}

	// 检查 HTTP 状态码
	if resp.StatusCode != http.StatusOK {
		// 尝试解析错误信息
		var errorResp struct {
			Message string `json:"message"`
		}
		if err := json.Unmarshal(respBody, &errorResp); err == nil && errorResp.Message != "" {
			return nil, fmt.Errorf("API 返回错误: %s (状态码: %d)", errorResp.Message, resp.StatusCode)
		}
		return nil, fmt.Errorf("API 请求失败，状态码: %d, 响应: %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}
