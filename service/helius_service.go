package service

import (
	"context"

	"github.com/life2you/datas-go/handler"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/rpc"
	"go.uber.org/zap"
)

// StartHeliusService 启动Helius服务
func StartHeliusService() {
	// 在后台协程中处理连接和订阅
	go func() {
		// 连接WebSocket
		err := rpc.GlobalWebSocketClient.Connect(context.Background())
		if err != nil {
			logger.Fatal("连接WebSocket服务器失败", zap.Error(err))
			return
		}
		logger.Info("成功连接到Helius WebSocket服务")

		// 订阅区块
		subscriptionID, err := rpc.GlobalWebSocketClient.SlotSubscribe(handler.HeliusSlotHandler)
		if err != nil {
			logger.Fatal("订阅区块更新失败", zap.Error(err))
			return
		}
		logger.Info("成功订阅Helius区块更新", zap.Int("subscriptionID", subscriptionID))
	}()

	logger.Info("Helius服务已启动")
}
