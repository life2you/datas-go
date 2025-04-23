# Solana 区块解析器

这个项目是一个用Go语言编写的Solana区块链解析器，可以获取和解析Solana区块链上的区块和交易数据。

## 功能特性

- RPC客户端：与Solana节点通信，支持代理和自定义HTTP头
- 区块解析：解析区块数据和交易
- WebSocket订阅：实时接收链上事件的通知
- Redis存储：持久化存储区块数据，支持高效检索
- 交易解析：解析不同类型的交易和指令

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

## 许可证

MIT
 