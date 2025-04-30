package rpc

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/life2you/datas-go/configs"
)

const (
	// PumpPortalWSURL 是PumpPortal WebSocket API的URL
	PumpPortalWSURL = "wss://pumpportal.fun/api/data"
)

// PumpPortalClient 表示PumpPortal WebSocket客户端
type PumpPortalClient struct {
	conn            *websocket.Conn
	url             string
	handler         MessageHandler
	handlersMutex   sync.RWMutex
	done            chan struct{}
	reconnect       bool
	reconnectMutex  sync.Mutex
	reconnectTicker *time.Ticker
	reconnectDelay  time.Duration
	closed          bool
	connMutex       sync.Mutex
	proxyURL        string
}

// PumpPortalMessage 表示从PumpPortal接收到的消息
type PumpPortalMessage struct {
	TxType string `json:"txType"`
}

// SubscribeRequest 表示订阅请求
type SubscribeRequest struct {
	Method string   `json:"method"`
	Keys   []string `json:"keys,omitempty"`
}

// MessageHandler 是处理消息的函数类型
type MessageHandler func(message json.RawMessage)

// PumpPortalOptions 包含PumpPortal WebSocket客户端的配置选项

// DefaultPumpPortalOptions 返回默认的PumpPortal选项
func DefaultPumpPortalOptions() *configs.PumpPortalOptions {
	return &configs.PumpPortalOptions{
		ReconnectDelay:  5 * time.Second,
		MaxRetryAttempt: 10,
	}
}

var GlobalPumpPortalClient *PumpPortalClient

// NewPumpPortalClient 创建一个新的PumpPortal客户端
func NewPumpPortalClient(options *configs.PumpPortalOptions, handler MessageHandler) {
	if options == nil {
		options = DefaultPumpPortalOptions()
	}
	if handler == nil {
		panic("handler cannot be nil")
	}
	GlobalPumpPortalClient = &PumpPortalClient{
		url:            PumpPortalWSURL,
		handler:        handler,
		done:           make(chan struct{}),
		reconnect:      true,
		reconnectDelay: options.ReconnectDelay,
		proxyURL:       options.ProxyURL,
	}
}

// Connect 建立WebSocket连接
func (c *PumpPortalClient) Connect(ctx context.Context) error {
	c.connMutex.Lock()
	defer c.connMutex.Unlock()

	if c.closed {
		return fmt.Errorf("客户端已关闭")
	}

	// 如果已经连接，就不需要再次连接
	if c.conn != nil {
		return nil
	}

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
		}
		log.Printf("使用代理连接PumpPortal WebSocket: %s", c.proxyURL)
	}

	// 建立连接
	conn, _, err := dialer.DialContext(ctx, u.String(), nil)
	if err != nil {
		return fmt.Errorf("连接PumpPortal WebSocket服务器失败: %w", err)
	}

	c.conn = conn
	log.Printf("成功连接到PumpPortal WebSocket服务器")

	// 启动消息接收循环
	go c.readLoop()

	// 启动心跳检测
	go c.pingLoop()

	return nil
}

// Close 关闭WebSocket连接
func (c *PumpPortalClient) Close() error {
	c.connMutex.Lock()
	defer c.connMutex.Unlock()

	if c.closed {
		return nil
	}

	c.closed = true
	close(c.done)
	c.reconnect = false

	// 停止重连计时器
	if c.reconnectTicker != nil {
		c.reconnectTicker.Stop()
	}

	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// 读取消息的循环
func (c *PumpPortalClient) readLoop() {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("PumpPortal WebSocket读取循环发生意外: %v", r)
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
				log.Printf("读取PumpPortal WebSocket消息错误: %v", err)
				return
			}

			var msg PumpPortalMessage
			if err := json.Unmarshal(message, &msg); err != nil {
				log.Printf("解析PumpPortal WebSocket消息错误: %v", err)
				continue
			}

			// 根据消息类型调用相应的处理函数
			c.handlersMutex.RLock()
			go c.handler(message)
			c.handlersMutex.RUnlock()
		}
	}
}

// 处理断开连接的逻辑
func (c *PumpPortalClient) handleDisconnect() {
	c.connMutex.Lock()

	// 如果客户端已关闭或不需要重连，直接返回
	if c.closed || !c.reconnect {
		c.connMutex.Unlock()
		return
	}

	// 清理旧连接
	if c.conn != nil {
		c.conn.Close()
		c.conn = nil
	}
	c.connMutex.Unlock()

	c.reconnectMutex.Lock()
	defer c.reconnectMutex.Unlock()

	// 如果重连计时器已存在，先停止它
	if c.reconnectTicker != nil {
		c.reconnectTicker.Stop()
	}

	// 启动重连计时器
	c.reconnectTicker = time.NewTicker(c.reconnectDelay)
	go func() {
		for {
			select {
			case <-c.done:
				return
			case <-c.reconnectTicker.C:
				ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
				if err := c.Connect(ctx); err != nil {
					log.Printf("重连PumpPortal WebSocket失败: %v, 将在%v后重试", err, c.reconnectDelay)
					cancel()
					continue
				}
				cancel()
				// 重连成功后重新订阅
				c.resubscribe()
				c.reconnectTicker.Stop()
				return
			}
		}
	}()
}

// 重新订阅之前的所有订阅
func (c *PumpPortalClient) resubscribe() {
	// 由于PumpPortal不保存订阅状态，需要调用者自行保存订阅状态并重新订阅
	log.Printf("已重连PumpPortal WebSocket，请重新订阅所需的数据流")
}

// pingLoop 维持连接活跃
func (c *PumpPortalClient) pingLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-c.done:
			return
		case <-ticker.C:
			c.connMutex.Lock()
			if c.conn == nil {
				c.connMutex.Unlock()
				return
			}
			if err := c.conn.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(10*time.Second)); err != nil {
				log.Printf("PumpPortal WebSocket发送ping失败: %v", err)
				c.connMutex.Unlock()
				c.handleDisconnect()
				return
			}
			c.connMutex.Unlock()
		}
	}
}

// sendRequest 发送请求到WebSocket服务器
func (c *PumpPortalClient) sendRequest(request interface{}) error {
	c.connMutex.Lock()
	defer c.connMutex.Unlock()

	if c.conn == nil {
		return fmt.Errorf("WebSocket连接未建立")
	}

	data, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("序列化请求失败: %w", err)
	}

	if err := c.conn.WriteMessage(websocket.TextMessage, data); err != nil {
		return fmt.Errorf("发送WebSocket消息失败: %w", err)
	}

	return nil
}

// SubscribeNewToken 订阅新代币创建事件
func (c *PumpPortalClient) SubscribeNewToken() error {
	request := SubscribeRequest{
		Method: "subscribeNewToken",
	}
	// 发送订阅请求
	return c.sendRequest(request)
}

// UnsubscribeNewToken 取消订阅新代币创建事件
func (c *PumpPortalClient) UnsubscribeNewToken() error {
	request := SubscribeRequest{
		Method: "unsubscribeNewToken",
	}
	// 发送取消订阅请求
	return c.sendRequest(request)
}

// SubscribeTokenTrade 订阅指定代币的交易事件
func (c *PumpPortalClient) SubscribeTokenTrade(tokenAddresses []string) error {
	request := SubscribeRequest{
		Method: "subscribeTokenTrade",
		Keys:   tokenAddresses,
	}
	// 发送订阅请求
	return c.sendRequest(request)
}

// UnsubscribeTokenTrade 取消订阅指定代币的交易事件
func (c *PumpPortalClient) UnsubscribeTokenTrade(tokenAddresses []string) error {
	request := SubscribeRequest{
		Method: "unsubscribeTokenTrade",
		Keys:   tokenAddresses,
	}
	// 发送取消订阅请求
	return c.sendRequest(request)
}

// SubscribeAccountTrade 订阅指定账户的交易事件
func (c *PumpPortalClient) SubscribeAccountTrade(accountAddresses []string) error {
	request := SubscribeRequest{
		Method: "subscribeAccountTrade",
		Keys:   accountAddresses,
	}
	// 发送订阅请求
	return c.sendRequest(request)
}

// UnsubscribeAccountTrade 取消订阅指定账户的交易事件
func (c *PumpPortalClient) UnsubscribeAccountTrade(accountAddresses []string) error {
	request := SubscribeRequest{
		Method: "unsubscribeAccountTrade",
		Keys:   accountAddresses,
	}
	// 发送取消订阅请求
	return c.sendRequest(request)
}

// SubscribeMigration 订阅代币迁移事件
func (c *PumpPortalClient) SubscribeMigration() error {
	request := SubscribeRequest{
		Method: "subscribeMigration",
	}
	// 发送订阅请求
	return c.sendRequest(request)
}
