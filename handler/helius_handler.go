package handler

import (
	"context"
	"encoding/json"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/storage"
	"go.uber.org/zap"
)

// HeliusSlotHandler 处理来自 Helius blockSubscribe 的 WebSocket 消息
// 它解析区块数据并将其存储到 Redis 中
func HeliusSlotHandler(result json.RawMessage) {
	var slotInfo struct {
		Parent uint64 `json:"parent"`
		Root   uint64 `json:"root"`
		Slot   uint64 `json:"slot"`
	}

	if err := json.Unmarshal(result, &slotInfo); err != nil {
		logger.Error("解析槽位数据失败", zap.Error(err))
		return
	}

	logger.Info("收到新槽位通知", zap.Uint64("slot", slotInfo.Slot))

	storage.GlobalRedisClient.StoreBlock(context.Background(), slotInfo.Slot)
}
