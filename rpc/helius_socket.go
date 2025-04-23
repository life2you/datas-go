package rpc

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"crypto/tls"

	"github.com/gorilla/websocket"
	"github.com/life2you/datas-go/configs"
)

// WebSocketClient 表示Helius WebSocket客户端
type WebSocketClient struct {
	conn              *websocket.Conn
	url               string
	apiKey            string
	subscriptions     map[string]SubscriptionHandler
	subscriptionMutex sync.Mutex
	nextID            int
	done              chan struct{}
	reconnect         bool
	reconnectInterval time.Duration
	onConnect         func()
	closed            bool
	mutex             sync.Mutex
	proxyURL          string
}

// SubscriptionHandler 是处理订阅响应的回调接口
type SubscriptionHandler func(result json.RawMessage)

// WebSocketOptions 包含WebSocket客户端的配置选项
type WebSocketOptions struct {
	ReconnectInterval time.Duration // 重连间隔时间
	OnConnect         func()        // 连接建立时的回调函数
	ProxyURL          string        // 代理服务器URL
}

var GlobalWebSocketClient *WebSocketClient

// NewWebSocketClientOptions 创建带有自定义选项的WebSocket客户端
func NewWebSocketClientOptions(config *configs.WebSocketConfig) {
	if config.NetworkType != "mainnet" && config.NetworkType != "devnet" {
		panic(fmt.Errorf("不支持的网络: %s, 请使用 'mainnet' 或 'devnet'", config.NetworkType))
	}

	baseURL := fmt.Sprintf("wss://%s.helius-rpc.com", config.NetworkType)
	endpoint := fmt.Sprintf("%s/?api-key=%s", baseURL, config.APIKey)

	reconnectInterval := config.ReconnectInterval
	if reconnectInterval == 0 {
		reconnectInterval = 5 * time.Second
	}

	client := &WebSocketClient{
		url:               endpoint,
		apiKey:            config.APIKey,
		subscriptions:     make(map[string]SubscriptionHandler),
		nextID:            1,
		done:              make(chan struct{}),
		reconnect:         true,
		reconnectInterval: reconnectInterval,
		onConnect:         config.OnConnect,
		proxyURL:          config.ProxyURL,
	}
	GlobalWebSocketClient = client
}

// Connect 建立WebSocket连接
func (c *WebSocketClient) Connect(ctx context.Context) error {
	c.mutex.Lock()
	if c.closed {
		c.mutex.Unlock()
		return fmt.Errorf("客户端已关闭")
	}
	c.mutex.Unlock()

	// 解析URL
	u, err := url.Parse(c.url)
	if err != nil {
		return fmt.Errorf("解析WebSocket URL失败: %w", err)
	}

	// 设置拨号选项
	dialer := websocket.DefaultDialer

	// 如果配置了代理，设置代理
	if c.proxyURL != "" {
		proxyURL, err := url.Parse(c.proxyURL)
		if err != nil {
			return fmt.Errorf("解析代理URL失败: %w", err)
		}
		dialer = &websocket.Dialer{
			Proxy:            http.ProxyURL(proxyURL),
			HandshakeTimeout: 45 * time.Second,
			TLSClientConfig:  &tls.Config{InsecureSkipVerify: true}, // 注意：在生产环境中不建议跳过TLS验证
		}
		log.Printf("使用代理连接WebSocket: %s", c.proxyURL)
	}

	// 建立连接
	conn, _, err := dialer.DialContext(ctx, u.String(), nil)
	if err != nil {
		return fmt.Errorf("连接WebSocket服务器失败: %w", err)
	}

	c.mutex.Lock()
	c.conn = conn
	c.mutex.Unlock()

	// 如果有连接回调，执行它
	if c.onConnect != nil {
		c.onConnect()
	}

	// 启动消息接收循环
	go c.readLoop()

	// 启动心跳检测
	go c.pingLoop()

	return nil
}

// Close 关闭WebSocket连接
func (c *WebSocketClient) Close() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if c.closed {
		return nil
	}

	c.closed = true
	close(c.done)
	c.reconnect = false

	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// 读取消息的循环
func (c *WebSocketClient) readLoop() {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("WebSocket读取循环发生意外: %v", r)
		}
		c.handleDisconnect()
	}()

	for {
		select {
		case <-c.done:
			return
		default:
			_, message, err := c.conn.ReadMessage()
			if err != nil {
				log.Printf("读取WebSocket消息错误: %v", err)
				return
			}

			// 解析响应
			var response struct {
				JSONRPC string          `json:"jsonrpc"`
				Method  string          `json:"method,omitempty"`
				Params  json.RawMessage `json:"params,omitempty"`
				Result  json.RawMessage `json:"result,omitempty"`
				ID      *int            `json:"id"`
				Error   *struct {
					Code    int    `json:"code"`
					Message string `json:"message"`
				} `json:"error,omitempty"`
			}

			if err := json.Unmarshal(message, &response); err != nil {
				log.Printf("解析WebSocket响应错误: %v", err)
				continue
			}

			// 处理订阅通知
			if response.Method != "" {
				var notification struct {
					Subscription int             `json:"subscription"`
					Result       json.RawMessage `json:"result"`
				}
				if err := json.Unmarshal(response.Params, &notification); err != nil {
					log.Printf("解析订阅通知错误: %v", err)
					continue
				}

				c.subscriptionMutex.Lock()
				handler, exists := c.subscriptions[response.Method]
				c.subscriptionMutex.Unlock()

				if exists {
					go handler(notification.Result)
				}
			} else if response.ID != nil {
				// 处理订阅响应
				// 响应可能包含订阅ID，需要存储以便后续处理通知
				if response.Result != nil {
					var subscriptionID int
					if err := json.Unmarshal(response.Result, &subscriptionID); err == nil {
						// 成功解析到订阅ID
						log.Printf("已接收订阅确认，ID: %d", subscriptionID)
					}
				}

				// 处理错误响应
				if response.Error != nil {
					log.Printf("WebSocket响应错误: 代码=%d, 消息=%s", response.Error.Code, response.Error.Message)
				}
			}
		}
	}
}

// 处理断开连接的逻辑
func (c *WebSocketClient) handleDisconnect() {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	// 如果客户端已关闭或不需要重连，直接返回
	if c.closed || !c.reconnect {
		return
	}

	// 清理旧连接
	if c.conn != nil {
		c.conn.Close()
		c.conn = nil
	}

	// 尝试重新连接
	go func() {
		log.Printf("WebSocket连接已断开，%v后尝试重连...", c.reconnectInterval)
		time.Sleep(c.reconnectInterval)

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := c.Connect(ctx); err != nil {
			log.Printf("WebSocket重连失败: %v", err)
			// 再次触发断开处理，以便继续尝试重连
			c.handleDisconnect()
		} else {
			log.Println("WebSocket重连成功")

			// 连接成功后重新订阅
			c.resubscribe()
		}
	}()
}

// 重新订阅所有活跃的订阅
func (c *WebSocketClient) resubscribe() {
	// 这里应该实现重新订阅的逻辑
	// 由于每个订阅都需要特定的参数，这里需要根据实际情况来实现
	// 此处仅为示例，实际项目中可能需要更复杂的实现
	log.Println("正在重新建立之前的订阅...")
}

// 定期发送ping以保持连接活跃
func (c *WebSocketClient) pingLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-c.done:
			return
		case <-ticker.C:
			c.mutex.Lock()
			if c.conn != nil {
				if err := c.conn.WriteMessage(websocket.PingMessage, []byte{}); err != nil {
					log.Printf("发送ping消息失败: %v", err)
					c.mutex.Unlock()
					c.handleDisconnect()
					return
				}
				log.Println("已发送ping")
			}
			c.mutex.Unlock()
		}
	}
}

// 生成唯一的请求ID
func (c *WebSocketClient) getNextID() int {
	c.subscriptionMutex.Lock()
	defer c.subscriptionMutex.Unlock()
	id := c.nextID
	c.nextID++
	return id
}

// subscribe 是所有订阅方法的基础方法
func (c *WebSocketClient) subscribe(method string, params []interface{}, handler SubscriptionHandler) (int, error) {
	c.mutex.Lock()
	if c.conn == nil {
		c.mutex.Unlock()
		return 0, fmt.Errorf("WebSocket连接未建立")
	}
	c.mutex.Unlock()

	requestID := c.getNextID()
	request := struct {
		JSONRPC string        `json:"jsonrpc"`
		ID      int           `json:"id"`
		Method  string        `json:"method"`
		Params  []interface{} `json:"params"`
	}{
		JSONRPC: "2.0",
		ID:      requestID,
		Method:  method,
		Params:  params,
	}

	// 发送订阅请求
	c.mutex.Lock()
	err := c.conn.WriteJSON(request)
	c.mutex.Unlock()
	if err != nil {
		return 0, fmt.Errorf("发送订阅请求失败: %w", err)
	}

	// 存储订阅处理器
	// 注意：这里我们暂时使用请求ID作为订阅ID的占位符
	// 实际上，服务器返回的订阅ID可能不同，需要在响应中更新
	c.subscriptionMutex.Lock()
	c.subscriptions["slotNotification"] = handler
	c.subscriptionMutex.Unlock()
	return requestID, nil
}

// unsubscribe 取消指定的订阅
func (c *WebSocketClient) unsubscribe(method string, subscriptionName string) error {
	c.mutex.Lock()
	if c.conn == nil {
		c.mutex.Unlock()
		return fmt.Errorf("WebSocket连接未建立")
	}
	c.mutex.Unlock()

	requestID := c.getNextID()
	request := struct {
		JSONRPC string        `json:"jsonrpc"`
		ID      int           `json:"id"`
		Method  string        `json:"method"`
		Params  []interface{} `json:"params"`
	}{
		JSONRPC: "2.0",
		ID:      requestID,
		Method:  method,
		Params:  []interface{}{subscriptionName},
	}

	// 发送取消订阅请求
	c.mutex.Lock()
	err := c.conn.WriteJSON(request)
	c.mutex.Unlock()
	if err != nil {
		return fmt.Errorf("发送取消订阅请求失败: %w", err)
	}

	// 从订阅映射中移除
	c.subscriptionMutex.Lock()
	delete(c.subscriptions, subscriptionName)
	c.subscriptionMutex.Unlock()

	return nil
}

// ProgramSubscribe 订阅程序账户变更
func (c *WebSocketClient) ProgramSubscribe(programID string, encoding string, handler SubscriptionHandler) (int, error) {
	params := []interface{}{
		programID,
		map[string]string{
			"encoding": encoding,
		},
	}
	return c.subscribe("programSubscribe", params, handler)
}

// ProgramUnsubscribe 取消程序账户订阅
func (c *WebSocketClient) ProgramUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("programUnsubscribe", "")
}

// SignatureSubscribe 订阅交易签名状态
func (c *WebSocketClient) SignatureSubscribe(signature string, commitment string, enableReceivedNotification bool, handler SubscriptionHandler) (int, error) {
	params := []interface{}{
		signature,
		map[string]interface{}{
			"commitment":                 commitment,
			"enableReceivedNotification": enableReceivedNotification,
		},
	}
	return c.subscribe("signatureSubscribe", params, handler)
}

// SignatureUnsubscribe 取消交易签名订阅
func (c *WebSocketClient) SignatureUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("signatureUnsubscribe", "")
}

// AccountSubscribe 订阅账户变更
func (c *WebSocketClient) AccountSubscribe(accountPubkey string, encoding string, commitment string, handler SubscriptionHandler) (int, error) {
	params := []interface{}{
		accountPubkey,
		map[string]string{
			"encoding":   encoding,
			"commitment": commitment,
		},
	}
	return c.subscribe("accountSubscribe", params, handler)
}

// AccountUnsubscribe 取消账户订阅
func (c *WebSocketClient) AccountUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("accountUnsubscribe", "")
}

// SlotSubscribe 订阅插槽更新
func (c *WebSocketClient) SlotSubscribe(handler SubscriptionHandler) (int, error) {
	return c.subscribe("slotSubscribe", []interface{}{}, handler)
}

// SlotUnsubscribe 取消插槽订阅
func (c *WebSocketClient) SlotUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("slotUnsubscribe", "slotNotification")
}

// LogsSubscribe 订阅日志
func (c *WebSocketClient) LogsSubscribe(filter interface{}, commitment string, handler SubscriptionHandler) (int, error) {
	params := []interface{}{
		filter,
		map[string]string{
			"commitment": commitment,
		},
	}
	return c.subscribe("logsSubscribe", params, handler)
}

// LogsUnsubscribe 取消日志订阅
func (c *WebSocketClient) LogsUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("logsUnsubscribe", "")
}

// BlockSubscribe 订阅区块更新
// 参数:
//   - filter: 过滤器类型，只能是 "all" 或 "mentionsAccountOrProgram"
//   - handler: 处理区块更新的回调函数
//
// 返回:
//   - int: 订阅ID
//   - error: 错误信息
func (c *WebSocketClient) BlockSubscribe(filter string, handler SubscriptionHandler) (int, error) {
	// 验证filter参数
	if filter != "all" && !strings.HasPrefix(filter, "mentionsAccountOrProgram") {
		log.Printf("警告: 区块订阅过滤器 '%s' 可能不被支持，有效值为 'all' 或 'mentionsAccountOrProgram'", filter)
	}

	// 构建参数
	params := []interface{}{filter}

	log.Printf("开始订阅区块更新，过滤器: %s", filter)
	return c.subscribe("blockSubscribe", params, handler)
}

// BlockUnsubscribe 取消区块订阅
func (c *WebSocketClient) BlockUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("blockUnsubscribe", "")
}

// RootSubscribe 订阅根节点更新
func (c *WebSocketClient) RootSubscribe(handler SubscriptionHandler) (int, error) {
	return c.subscribe("rootSubscribe", []interface{}{}, handler)
}

// RootUnsubscribe 取消根节点订阅
func (c *WebSocketClient) RootUnsubscribe(subscriptionID int) error {
	return c.unsubscribe("rootUnsubscribe", "")
}
