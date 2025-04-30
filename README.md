# Solana 区块解析器

这个项目是一个用Go语言编写的Solana区块链解析器，可以获取和解析Solana区块链上的区块和交易数据。

## 功能特性

- RPC客户端：与Solana节点通信，支持代理和自定义HTTP头
- 区块解析：解析区块数据和交易
- WebSocket订阅：实时接收链上事件的通知
- Redis存储：持久化存储区块数据，支持高效检索
- 交易解析：解析不同类型的交易和指令
- Helius API：支持高级区块链数据查询和丰富的交易数据
- Helius Webhook：支持监控Solana区块链上的事件，并在事件发生时通过回调URL接收通知

## 安装

```bash
go get github.com/life2you/datas-go
```

## 使用方法

### RPC客户端

```go
package main

import (
    "context"
    "fmt"
    "log"
    
    "github.com/life2you/datas-go/rpc"
)

func main() {
    // 创建RPC客户端
    client := rpc.NewClient("https://api.mainnet-beta.solana.com")
    
    // 获取最新区块高度
    ctx := context.Background()
    slot, err := client.GetLatestBlockHeight(ctx)
    if err != nil {
        log.Fatalf("获取最新区块高度失败: %v", err)
    }
    fmt.Printf("最新区块高度: %d\n", slot)
    
    // 获取区块数据
    block, err := client.GetBlock(ctx, slot)
    if err != nil {
        log.Fatalf("获取区块数据失败: %v", err)
    }
    fmt.Printf("区块哈希: %s, 交易数量: %d\n", block.Blockhash, len(block.Transactions))
}
```

### Helius API 客户端

Helius API 提供了增强的 Solana 数据查询功能，包括交易解析和丰富的交易历史查询。

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    
    "github.com/life2you/datas-go/rpc"
)

func main() {
    // 获取 Helius API 密钥
    apiKey := os.Getenv("HELIUS_API_KEY")
    if apiKey == "" {
        log.Fatal("请设置 HELIUS_API_KEY 环境变量")
    }
    
    // 创建 Helius 客户端
    heliusClient := rpc.NewHeliusClient("https://api.helius.xyz/v0", apiKey)
    
    ctx := context.Background()
    
    // 解析交易
    txSignatures := []string{
        "2UcHTFpDv2equZPFpkrmsXCuZ7ZBygxsrXpzNy1xCaLCaAPcyi8vXnzGgFW8ygLEu4brECXTY8XrZEGW8vYGfcqD",
        "5L8r6xSKCBgP2vQBgFLN6Z9KvpicyEBxyeQB4y76xXC5Syh1iJBvyKvvEnxXwYtKrRo2nVe5vDQ2QTCKmyRqrBeV",
    }
    
    parsedTxs, err := heliusClient.ParseTransactions(ctx, txSignatures)
    if err != nil {
        log.Fatalf("解析交易失败: %v", err)
    }
    
    for i, tx := range parsedTxs {
        fmt.Printf("交易 %s 解析结果:\n", txSignatures[i])
        fmt.Printf("  类型: %s\n", tx.Type)
        fmt.Printf("  描述: %s\n", tx.Description)
        fmt.Printf("  费用: %d lamports\n", tx.Fee)
        fmt.Printf("  状态: %s\n\n", tx.Status)
    }
    
    // 获取丰富的交易历史
    walletAddress := "Your_Wallet_Address"
    
    options := rpc.EnrichedHistoryOptions{
        Limit: 10,
        Types: []string{"SWAP", "NFT_SALE"},
    }
    
    history, err := heliusClient.GetEnrichedTransactionHistory(ctx, walletAddress, options)
    if err != nil {
        log.Fatalf("获取交易历史失败: %v", err)
    }
    
    fmt.Printf("地址 %s 的交易历史:\n", walletAddress)
    for _, tx := range history {
        fmt.Printf("  签名: %s\n", tx.Signature)
        fmt.Printf("  类型: %s\n", tx.Type)
        fmt.Printf("  时间戳: %d\n", tx.Timestamp)
        fmt.Printf("  描述: %s\n\n", tx.Description)
    }
}
```

### WebSocket客户端

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "os"
    "time"
    
    "github.com/life2you/datas-go/rpc"
)

func main() {
    // 从环境变量获取API密钥
    apiKey := os.Getenv("HELIUS_API_KEY")
    if apiKey == "" {
        log.Fatal("请设置HELIUS_API_KEY环境变量")
    }
    
    // 创建WebSocket客户端
    client, err := rpc.NewWebSocketClient("mainnet", apiKey)
    if err != nil {
        log.Fatalf("创建WebSocket客户端失败: %v", err)
    }
    
    // 连接WebSocket服务器
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    if err := client.Connect(ctx); err != nil {
        log.Fatalf("连接WebSocket服务器失败: %v", err)
    }
    
    // 订阅插槽更新
    slotSubID, err := client.SlotSubscribe(func(result json.RawMessage) {
        var slotInfo struct {
            Parent uint64 `json:"parent"`
            Root   uint64 `json:"root"`
            Slot   uint64 `json:"slot"`
        }
        if err := json.Unmarshal(result, &slotInfo); err != nil {
            log.Printf("解析插槽数据失败: %v", err)
            return
        }
        log.Printf("新插槽: %d", slotInfo.Slot)
    })
    if err != nil {
        log.Fatalf("订阅插槽更新失败: %v", err)
    }
    
    // 保持程序运行
    time.Sleep(5 * time.Minute)
    
    // 取消订阅
    if err := client.SlotUnsubscribe(slotSubID); err != nil {
        log.Printf("取消插槽订阅失败: %v", err)
    }
    
    // 关闭连接
    client.Close()
}

### PumpPortal WebSocket客户端

PumpPortal WebSocket客户端提供了实时订阅PumpPortal数据API，用于接收代币创建、交易等实时数据。

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/life2you/datas-go/rpc"
)

func main() {
	// 创建PumpPortal客户端
	options := rpc.DefaultPumpPortalOptions()
	client := rpc.NewPumpPortalClient(options)

	// 建立连接
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := client.Connect(ctx); err != nil {
		log.Fatalf("连接PumpPortal失败: %v", err)
	}
	defer client.Close()

	// 处理新代币创建事件
	newTokenHandler := func(data json.RawMessage) {
		var token map[string]interface{}
		if err := json.Unmarshal(data, &token); err != nil {
			log.Printf("解析新代币数据失败: %v", err)
			return
		}
		log.Printf("收到新代币创建事件: %+v", token)
	}

	// 订阅新代币创建
	if err := client.SubscribeNewToken(newTokenHandler); err != nil {
		log.Printf("订阅新代币创建失败: %v", err)
	}

	// 订阅特定代币的交易
	tokenAddresses := []string{"91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p"}
	if err := client.SubscribeTokenTrade(tokenAddresses, func(data json.RawMessage) {
		var trade map[string]interface{}
		json.Unmarshal(data, &trade)
		log.Printf("收到代币交易事件: %+v", trade)
	}); err != nil {
		log.Printf("订阅代币交易失败: %v", err)
	}

	// 等待中断信号退出
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	// 取消订阅
	client.UnsubscribeNewToken()
	client.UnsubscribeTokenTrade(tokenAddresses)
}
```

### Redis存储

Redis存储服务用于持久化存储Solana区块数据，支持高效检索和查询。

```go
package main

import (
    "context"
    "log"
    
    "github.com/life2you/datas-go/storage"
)

func main() {
    // 创建Redis客户端
    redis, err := storage.NewDefaultRedisClient()
    if err != nil {
        log.Fatalf("初始化Redis客户端失败: %v", err)
    }
    defer redis.Close()
    
    ctx := context.Background()
    
    // 获取最小区块高度
    minSlot, minBlock, err := redis.GetMinBlock(ctx)
    if err == nil {
        log.Printf("最小区块高度: %d, 哈希: %s", minSlot, minBlock.Blockhash)
    }
    
    // 获取最大区块高度
    maxSlot, maxBlock, err := redis.GetMaxBlock(ctx)
    if err == nil {
        log.Printf("最大区块高度: %d, 哈希: %s", maxSlot, maxBlock.Blockhash)
    }
    
    // 获取存储的区块总数
    count, _ := redis.GetBlockCount(ctx)
    log.Printf("存储的区块总数: %d", count)
}
```

自定义Redis连接选项：

```go
options := storage.RedisOptions{
    Addr:     "redis.example.com:6379",
    Password: "your-password",
    DB:       0,
    PoolSize: 20,
}

redis, err := storage.NewRedisClient(options)
```

## WebSocket订阅类型

该客户端支持以下Solana WebSocket订阅类型：

1. **账户订阅**：监控特定账户的变更
   ```go
   client.AccountSubscribe(accountPubkey, "jsonParsed", "finalized", handler)
   ```

2. **程序订阅**：监控特定程序的所有账户变更
   ```go
   client.ProgramSubscribe(programID, "jsonParsed", handler)
   ```

3. **插槽订阅**：监控新区块插槽
   ```go
   client.SlotSubscribe(handler)
   ```

4. **签名订阅**：监控特定交易签名的状态
   ```go
   client.SignatureSubscribe(signature, "finalized", false, handler)
   ```

5. **日志订阅**：监控满足特定条件的日志
   ```go
   client.LogsSubscribe("all", "finalized", handler) // 监控所有日志
   client.LogsSubscribe({mentionsAccountId: "your-account-id"}, "finalized", handler) // 监控特定账户相关的日志
   ```

6. **区块订阅**：监控新的区块并处理区块数据
   ```go
   client.BlockSubscribe("finalized", handler) // 只接收已确认的区块
   ```

## Helius API 高级功能

Helius API 提供以下高级功能：

### 1. 交易解析 (ParseTransactions)

解析交易签名为结构化数据，包含丰富的交易详情：

```go
parsedTxs, err := heliusClient.ParseTransactions(ctx, []string{"transaction-signature"})
```

解析结果包含：
- 交易类型（转账、交换、NFT 销售等）
- 交易描述
- 交易状态
- 费用详情
- 账户列表
- 代币转移详情
- 原始交易数据

### 2. 丰富的交易历史 (GetEnrichedTransactionHistory)

获取钱包地址的丰富交易历史：

```go
options := rpc.EnrichedHistoryOptions{
    Limit:     20,             // 返回的交易数量
    Before:    "tx-signature", // 分页：获取此签名之前的交易
    Types:     []string{"SWAP", "NFT_SALE"}, // 筛选交易类型
    SortOrder: "desc",         // 排序顺序：desc 或 asc
}

history, err := heliusClient.GetEnrichedTransactionHistory(ctx, "wallet-address", options)
```

支持的交易类型筛选：
- `NFT_MINT`：NFT 铸造
- `NFT_SALE`：NFT 销售
- `NFT_LISTING`：NFT 上架
- `NFT_CANCEL_LISTING`：取消 NFT 上架
- `NFT_AUCTION_CREATED`：NFT 拍卖创建
- `NFT_BID`：NFT 出价
- `NFT_AUCTION_COMPLETE`：NFT 拍卖完成
- `SWAP`：代币交换
- `TRANSFER`：代币或 SOL 转账
- ...更多类型

## 使用代理

本项目支持通过HTTP代理连接Solana节点和Helius WebSocket服务。

### 配置代理

在 `config.yaml` 中设置代理URL：

```yaml
# RPC客户端配置
rpc:
  endpoint: https://api.mainnet-beta.solana.com  # Solana RPC节点地址
  proxy_url: "http://your-proxy-server:port"     # 代理服务器URL

# WebSocket客户端配置
websocket:
  enabled: true
  network_type: mainnet
  api_key: "your-helius-api-key"
  proxy_url: "http://your-proxy-server:port"     # 代理服务器URL
  
# Helius API 配置
helius:
  endpoint: "https://api.helius.xyz/v0"
  api_key: "your-helius-api-key"
  proxy_url: "http://your-proxy-server:port"     # 代理服务器URL
```

通过代码设置代理：

```go
// 配置WebSocket
configs.GlobalConfig.WebSocket.ProxyURL = "http://your-proxy-server:port"

// 初始化WebSocket客户端
rpcClient, err := rpc.NewWebSocketClientOptions(&configs.GlobalConfig.WebSocket)
if err != nil {
    logger.Fatal("初始化WebSocket客户端失败", zap.Error(err))
}

// 配置Helius客户端
heliusClient := rpc.NewHeliusClient("https://api.helius.xyz/v0", "your-helius-api-key")
heliusClient.SetProxyURL("http://your-proxy-server:port")
```

### 注意事项

- 使用代理时，建议配置连接超时和重试机制。
- 在生产环境中，请确保代理服务器的安全性和可靠性。

## Redis存储功能

Redis存储服务提供以下主要功能：

1. **存储区块**: 将区块数据存储到Redis中
   ```go
   redis.StoreBlock(ctx, slot, block)
   ```

2. **获取区块**: 根据区块高度获取区块数据
   ```go
   block, err := redis.GetBlockBySlot(ctx, slot)
   ```

3. **获取最小/最大区块**: 获取已存储的最小或最大高度的区块
   ```go
   minSlot, minBlock, err := redis.GetMinBlock(ctx)
   maxSlot, maxBlock, err := redis.GetMaxBlock(ctx)
   ```

4. **删除区块**: 从存储中移除指定区块
   ```go
   redis.RemoveBlock(ctx, slot)
   ```

5. **检查区块是否存在**: 确认特定区块是否已存储
   ```go
   exists, err := redis.BlockExists(ctx, slot)
   ```

6. **获取存储统计**: 获取已存储区块的数量
   ```go
   count, err := redis.GetBlockCount(ctx)
   ```

7. **获取区块范围**: 获取指定范围内的区块高度列表
   ```go
   slots, err := redis.GetBlocksRange(ctx, 0, 9) // 获取前10个区块
   ```

## 错误处理与重连

WebSocket客户端内建自动重连机制，当连接断开时会自动尝试重新连接。此外，它还包含心跳机制以保持连接活跃。

## 自定义选项

可以通过自定义选项创建WebSocket客户端：

```go
options := rpc.WebSocketOptions{
    ReconnectInterval: 3 * time.Second,
    OnConnect: func() {
        log.Println("WebSocket连接已建立")
    },
}
client, err := rpc.NewWebSocketClientOptions("mainnet", apiKey, options)
```

## 交易解析功能

### Swap 交易解析

本项目支持将 Solana 区块链上的 Swap 交易解析为人类可读格式。

#### 功能特点

- 支持解析 SOL 与代币之间的交换交易
- 支持解析代币与代币之间的交换交易
- 格式化显示交易金额和代币单位
- 自动判断交易方向（买入/卖出）

#### 使用方法

```bash
# 通过命令行工具测试解析
go run cmd/parser/main.go --tx-type=SWAP --sample-file=./testdata/sample_swap.json
```

#### 代码示例

```go
// 解析 Swap 交易
func ParseSwapTransaction(tx *ParsedTransaction) string {
    if tx == nil || tx.Events == nil || tx.Events.Swap == nil {
        return "无效的Swap交易"
    }
    
    swap := tx.Events.Swap
    
    // 解析逻辑...
    
    if isBuy {
        return fmt.Sprintf("地址%s 用 %s SOL 购买了 %s个%s", 
            formatShortAddress(account), solValue, tokenValue, tokenMint)
    } else {
        return fmt.Sprintf("地址%s 卖出 %s个%s 获得了 %s SOL", 
            formatShortAddress(account), tokenValue, tokenMint, solValue)
    }
}
```

#### VS Code 调试配置

项目包含完整的 VS Code 调试配置，可以轻松调试解析功能：

1. 在 VS Code 中打开项目
2. 选择 "运行和调试" 面板
3. 从下拉菜单中选择 "调试交易解析" 或 "测试 Swap 解析器"
4. 按 F5 开始调试

## Helius Webhook 功能

Helius Webhook允许您监控Solana区块链上的事件，并在事件发生时通过回调URL接收通知。这个功能使您能够构建事件驱动的应用程序，对链上活动实时响应。

### 支持的事件类型

- NFT销售
- NFT上架
- NFT出价
- 代币交换
- 代币铸造
- 代币转账
- 等其他Solana链上事件

### 使用方法

#### 1. 配置

在配置文件`config.yaml`中添加Webhook配置:

```yaml
helius_webhook:
  api_key: "你的Helius API密钥"
  callback_url: "https://你的回调URL.com/webhook"
```

#### 2. 初始化Webhook客户端

```go
import (
    "github.com/life2you/datas-go/configs"
    "github.com/life2you/datas-go/rpc"
)

func main() {
    // 加载配置
    configs.LoadConfig("config.yaml")
    
    // 初始化Webhook客户端
    webhookClient := rpc.NewHeliusWebhookClient(&configs.GlobalConfig.HeliusWebhook)
    
    // ... 后续代码
}
```

#### 3. 创建Webhook

```go
webhook, err := webhookClient.CreateWebhook(rpc.Webhook{
    Webhook:          configs.GlobalConfig.HeliusWebhook.CallbackURL,
    WebhookType:      rpc.EnhancedWebhook,
    AccountAddresses: []string{"你要监控的Solana地址"},
    TransactionTypes: []rpc.TransactionType{
        rpc.TransactionTypeNFTSale,
        rpc.TransactionTypeTokenTransfer,
    },
})
if err != nil {
    log.Fatalf("创建Webhook失败: %v", err)
}
log.Printf("成功创建Webhook，ID: %s", webhook.ID)
```

#### 4. 处理接收到的Webhook事件

在您的HTTP服务器中设置处理Webhook的路由:

```go
import (
    "io"
    "net/http"
    
    "github.com/life2you/datas-go/rpc"
    "github.com/life2you/datas-go/logger"
)

func setupRoutes() {
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
        if err := rpc.HandleWebhookEvent(body, myCustomHandler); err != nil {
            logger.Error("处理Webhook事件失败", zap.Error(err))
            http.Error(w, "处理事件失败", http.StatusInternalServerError)
            return
        }

        // 返回成功
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    })
}

// 自定义处理函数
func myCustomHandler(events []rpc.WebhookEvent) error {
    for _, event := range events {
        // 处理事件...
        logger.Info("收到事件", 
            zap.String("类型", event.Type),
            zap.String("签名", event.Signature))
    }
    return nil
}
```

#### 5. 管理Webhook

```go
// 获取所有Webhook
webhooks, err := webhookClient.GetWebhooks()
if err != nil {
    log.Fatalf("获取Webhook列表失败: %v", err)
}

// 获取特定Webhook
webhook, err := webhookClient.GetWebhook("webhook-id")
if err != nil {
    log.Fatalf("获取Webhook失败: %v", err)
}

// 编辑Webhook
updatedWebhook, err := webhookClient.EditWebhook("webhook-id", rpc.Webhook{
    WebhookType:      rpc.EnhancedWebhook,
    AccountAddresses: []string{"新的监控地址"},
    TransactionTypes: []rpc.TransactionType{rpc.TransactionTypeAll},
})
if err != nil {
    log.Fatalf("编辑Webhook失败: %v", err)
}

// 删除Webhook
err = webhookClient.DeleteWebhook("webhook-id")
if err != nil {
    log.Fatalf("删除Webhook失败: %v", err)
}
```

### 使用场景

- **机器人操作**: 当NFT在特定市场上架时触发"NFT购买"操作
- **监控与警报**: 当程序发出特定日志时触发警报系统集成
- **事件驱动索引**: 将特定程序的任何交易直接发送到您的数据库或后端
- **通知与活动跟踪**: 在钱包间转账时发送通知
- **分析与日志**: 将事件发送到数据分析管道以查看趋势
- **工作流自动化**: 当特定事件发生时触发一系列操作

## 许可证

MIT
 