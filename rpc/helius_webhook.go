package rpc

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/life2you/datas-go/configs"
	"github.com/life2you/datas-go/logger"
	"go.uber.org/zap"
)

const (
	// HeliusWebhookBaseURL 是 Helius Webhook API 的基础 URL
	HeliusWebhookBaseURL = "https://api.helius.xyz/v0"
)

// WebhookType 定义 Webhook 的类型
type WebhookType string

const (
	// EnhancedWebhook 提供人类可读的已解析数据
	EnhancedWebhook WebhookType = "enhanced"
	// RawWebhook 提供原始交易数据
	RawWebhook WebhookType = "raw"
)

// TransactionType 定义支持的交易类型
type TransactionType string

const (
	// 所有交易类型
	TransactionTypeAll TransactionType = "all"
	// NFT 销售
	TransactionTypeNFTSale TransactionType = "NFT_SALE"
	// NFT 上架
	TransactionTypeNFTListing TransactionType = "NFT_LISTING"
	// NFT 出价
	TransactionTypeNFTBid TransactionType = "NFT_BID"
	// 代币交换
	TransactionTypeSwap TransactionType = "SWAP"
	// 代币铸造
	TransactionTypeTokenMint TransactionType = "TOKEN_MINT"
	// 代币转账
	TransactionTypeTokenTransfer TransactionType = "TOKEN_TRANSFER"
)

// Webhook 结构体表示 Helius Webhook 配置
type Webhook struct {
	ID               string            `json:"id,omitempty"`
	Webhook          string            `json:"webhook"`
	WebhookType      WebhookType       `json:"webhookType"`
	TransactionTypes []TransactionType `json:"transactionTypes,omitempty"`
	AccountAddresses []string          `json:"accountAddresses"`
	AuthHeader       string            `json:"authHeader,omitempty"`
}

// HeliusWebhookClient 是与 Helius Webhook API 交互的客户端
type HeliusWebhookClient struct {
	apiKey     string
	httpClient *http.Client
}

var GlobalHeliusWebhookClient *HeliusWebhookClient

// NewHeliusWebhookClient 创建一个新的 Helius Webhook 客户端
func NewHeliusWebhookClient(config *configs.HeliusWebhookConfig) *HeliusWebhookClient {
	// 创建一个带有超时设置的 HTTP 客户端
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	client := &HeliusWebhookClient{
		apiKey:     config.APIKey,
		httpClient: httpClient,
	}

	GlobalHeliusWebhookClient = client
	logger.Info("Helius Webhook 客户端初始化完成")

	return client
}

// CreateWebhook 创建一个新的 Webhook
func (c *HeliusWebhookClient) CreateWebhook(webhook Webhook) (*Webhook, error) {
	url := fmt.Sprintf("%s/webhooks?api-key=%s", HeliusWebhookBaseURL, c.apiKey)

	jsonData, err := json.Marshal(webhook)
	if err != nil {
		return nil, fmt.Errorf("marshal webhook: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("create webhook request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("create webhook failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result Webhook
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	logger.Info("成功创建 Webhook", zap.String("id", result.ID), zap.String("url", result.Webhook))
	return &result, nil
}

// GetWebhooks 获取所有的 Webhooks
func (c *HeliusWebhookClient) GetWebhooks() ([]Webhook, error) {
	url := fmt.Sprintf("%s/webhooks?api-key=%s", HeliusWebhookBaseURL, c.apiKey)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("get webhooks request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("get webhooks failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result []Webhook
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	logger.Info("成功获取 Webhooks", zap.Int("count", len(result)))
	return result, nil
}

// GetWebhook 获取特定 ID 的 Webhook
func (c *HeliusWebhookClient) GetWebhook(webhookID string) (*Webhook, error) {
	url := fmt.Sprintf("%s/webhooks/%s?api-key=%s", HeliusWebhookBaseURL, webhookID, c.apiKey)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("get webhook request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("get webhook failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result Webhook
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	logger.Info("成功获取 Webhook", zap.String("id", result.ID), zap.String("url", result.Webhook))
	return &result, nil
}

// EditWebhook 编辑已有的 Webhook
func (c *HeliusWebhookClient) EditWebhook(webhookID string, webhook Webhook) (*Webhook, error) {
	url := fmt.Sprintf("%s/webhooks/%s?api-key=%s", HeliusWebhookBaseURL, webhookID, c.apiKey)

	jsonData, err := json.Marshal(webhook)
	if err != nil {
		return nil, fmt.Errorf("marshal webhook: %w", err)
	}

	req, err := http.NewRequest(http.MethodPut, url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("create edit request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("edit webhook request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("edit webhook failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result Webhook
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	logger.Info("成功编辑 Webhook", zap.String("id", result.ID), zap.String("url", result.Webhook))
	return &result, nil
}

// DeleteWebhook 删除一个 Webhook
func (c *HeliusWebhookClient) DeleteWebhook(webhookID string) error {
	url := fmt.Sprintf("%s/webhooks/%s?api-key=%s", HeliusWebhookBaseURL, webhookID, c.apiKey)

	req, err := http.NewRequest(http.MethodDelete, url, nil)
	if err != nil {
		return fmt.Errorf("create delete request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("delete webhook request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("delete webhook failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	logger.Info("成功删除 Webhook", zap.String("id", webhookID))
	return nil
}

// WebhookEvent 表示 Webhook 接收到的事件数据结构
type WebhookEvent struct {
	AccountData     interface{}            `json:"accountData,omitempty"`
	Description     string                 `json:"description,omitempty"`
	Type            string                 `json:"type,omitempty"`
	Source          string                 `json:"source,omitempty"`
	Fee             int64                  `json:"fee,omitempty"`
	Signature       string                 `json:"signature,omitempty"`
	Slot            int64                  `json:"slot,omitempty"`
	Timestamp       int64                  `json:"timestamp,omitempty"`
	NativeTransfers []TransferData         `json:"nativeTransfers,omitempty"`
	TokenTransfers  []TokenTransferData    `json:"tokenTransfers,omitempty"`
	Events          map[string]interface{} `json:"events,omitempty"`
	Interactions    []string               `json:"interactions,omitempty"`
}

// TransferData 表示原生 SOL 转账数据
type TransferData struct {
	FromUserAccount string `json:"fromUserAccount"`
	ToUserAccount   string `json:"toUserAccount"`
	Amount          int64  `json:"amount"`
}

// TokenTransferData 表示代币转账数据
type TokenTransferData struct {
	FromUserAccount string `json:"fromUserAccount"`
	ToUserAccount   string `json:"toUserAccount"`
	Mint            string `json:"mint"`
	Amount          string `json:"amount"`
	TokenStandard   string `json:"tokenStandard,omitempty"`
}

// 处理 Webhook 事件的回调函数类型
type WebhookEventHandler func(event []WebhookEvent) error

// HandleWebhookEvent 处理从 Helius 接收到的 Webhook 事件
func HandleWebhookEvent(body []byte, handler WebhookEventHandler) error {
	var events []WebhookEvent

	if err := json.Unmarshal(body, &events); err != nil {
		logger.Error("解析 Webhook 事件失败", zap.Error(err))
		return fmt.Errorf("unmarshal webhook event: %w", err)
	}

	logger.Info("接收到 Webhook 事件", zap.Int("count", len(events)))
	return handler(events)
}

// ExampleWebhookHandler 是一个示例回调函数，展示如何处理Webhook事件
func ExampleWebhookHandler(events []WebhookEvent) error {
	for i, event := range events {
		logger.Info("处理Webhook事件",
			zap.Int("索引", i),
			zap.String("类型", event.Type),
			zap.String("签名", event.Signature),
			zap.Int64("槽位", event.Slot),
			zap.Time("时间", time.Unix(event.Timestamp, 0)),
		)

		// 处理原生SOL转账
		if len(event.NativeTransfers) > 0 {
			for _, transfer := range event.NativeTransfers {
				logger.Info("SOL转账",
					zap.String("从账户", transfer.FromUserAccount),
					zap.String("到账户", transfer.ToUserAccount),
					zap.Float64("数量", float64(transfer.Amount)/1e9), // 转换为SOL单位
				)
			}
		}

		// 处理代币转账
		if len(event.TokenTransfers) > 0 {
			for _, transfer := range event.TokenTransfers {
				logger.Info("代币转账",
					zap.String("从账户", transfer.FromUserAccount),
					zap.String("到账户", transfer.ToUserAccount),
					zap.String("代币", transfer.Mint),
					zap.String("数量", transfer.Amount),
				)
			}
		}
	}
	return nil
}

// SetupWebhookHandler 设置HTTP处理程序来接收Webhook事件
func SetupWebhookHandler(router interface{}) {
	// 这里只是一个示例，实际实现需要根据您使用的HTTP框架来调整
	// 例如，如果使用的是标准库的http包:
	/*
		http.HandleFunc("/webhook", func(w http.ResponseWriter, r *http.Request) {
			if r.Method != http.MethodPost {
				http.Error(w, "仅支持POST请求", http.StatusMethodNotAllowed)
				return
			}

			// 读取请求体
			body, err := io.ReadAll(r.Body)
			if err != nil {
				logger.Error("读取Webhook请求体失败", zap.Error(err))
				http.Error(w, "读取请求失败", http.StatusInternalServerError)
				return
			}
			defer r.Body.Close()

			// 处理Webhook事件
			if err := HandleWebhookEvent(body, ExampleWebhookHandler); err != nil {
				logger.Error("处理Webhook事件失败", zap.Error(err))
				http.Error(w, "处理事件失败", http.StatusInternalServerError)
				return
			}

			// 返回成功
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("OK"))
		})
	*/

	logger.Info("已设置Webhook处理程序")
}
