package handler

import (
	"context"
	"encoding/json"
	"time"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/storage" // 假设 storage 包提供了 Redis 客户端
	"go.uber.org/zap"
)

// HeliusBlockResult 定义了从 Helius blockSubscribe WebSocket 消息中解析的数据结构
// 参考: https://docs.helius.dev/rpc/websocket/blocksubscribe
type HeliusBlockResult struct {
	Block struct {
		BlockHeight       *uint64 `json:"blockHeight"` // 使用指针，因为可能为 null
		BlockTime         int64   `json:"blockTime"`
		Blockhash         string  `json:"blockhash"`
		ParentSlot        uint64  `json:"parentSlot"`
		PreviousBlockhash string  `json:"previousBlockhash"`
		// 暂时忽略 transactions 和 rewards 以避免存储过多数据
	} `json:"block"`
	Slot uint64 `json:"slot"`
}

// HeliusSlotHandler 处理来自 Helius blockSubscribe 的 WebSocket 消息
// 它解析区块数据并将其存储到 Redis 中
func HeliusSlotHandler(result json.RawMessage) {
	// blockSubscribe 返回的 result 是直接的区块数据
	// 但我们需要先检查是否有额外的包装，因为有时候 result 可能包含在其他结构中
	var blockData HeliusBlockResult
	err := json.Unmarshal(result, &blockData)

	// 如果解析失败，可能是因为消息格式与预期不同
	if err != nil || (blockData.Slot == 0 && blockData.Block.Blockhash == "") {
		// 尝试解析可能的包装格式
		var wrappedResult struct {
			Result HeliusBlockResult `json:"result"`
		}

		if unmarshalErr := json.Unmarshal(result, &wrappedResult); unmarshalErr == nil {
			// 从包装中提取区块数据
			blockData = wrappedResult.Result
		} else {
			logger.Logger.Error("无法解析 Helius 区块数据",
				zap.Error(err),
				zap.ByteString("raw_data", result),
				zap.Error(unmarshalErr))
			return
		}
	}

	// 检查关键数据是否存在
	if blockData.Slot == 0 || blockData.Block.Blockhash == "" {
		logger.Logger.Warn("收到的 Helius 区块数据缺少关键字段",
			zap.Uint64("slot", blockData.Slot),
			zap.String("blockhash", blockData.Block.Blockhash),
			zap.ByteString("raw_data", result))
		return
	}

	logger.Logger.Info("收到新的 Helius 区块",
		zap.Uint64("slot", blockData.Slot),
		zap.String("blockhash", blockData.Block.Blockhash),
		zap.Uint64("parentSlot", blockData.Block.ParentSlot),
		zap.Int64("blockTime", blockData.Block.BlockTime),
	)

	// 将区块数据（简化后）存储到 Redis
	// 使用 storage 包中定义的全局 Redis 客户端
	redisClient := storage.GlobalRedisClient
	if redisClient == nil {
		logger.Logger.Error("Redis 客户端尚未初始化")
		return
	}

	// 定义要存储的数据结构（可以根据需要调整）
	blockInfoToStore := map[string]interface{}{
		"slot":        blockData.Slot,
		"blockhash":   blockData.Block.Blockhash,
		"parentSlot":  blockData.Block.ParentSlot,
		"blockTime":   blockData.Block.BlockTime,
		"blockHeight": blockData.Block.BlockHeight, // 可能为 nil
		"receivedAt":  time.Now().Unix(),           // 添加接收时间戳
	}

	// 使用后台上下文
	ctx := context.Background()

	// 设置一个过期时间，例如 24 小时，防止 Redis 无限增长
	expiration := 24 * time.Hour

	// 使用 StoreHeliusBlock 方法存储区块信息
	err = redisClient.StoreHeliusBlock(ctx, blockData.Slot, blockInfoToStore, expiration)
	if err != nil {
		logger.Logger.Error("无法将区块信息存入 Redis", zap.Uint64("slot", blockData.Slot), zap.Error(err))
		return
	}

	logger.Logger.Debug("成功将区块信息存入 Redis", zap.Uint64("slot", blockData.Slot))
}
