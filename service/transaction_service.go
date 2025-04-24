package service

import (
	"github.com/life2you/datas-go/handler"
	"github.com/life2you/datas-go/logger"
)

// ProcessTransactionQueue 启动队列处理服务
func ProcessTransactionQueue() {
	go func() {
		// 等待系统初始化完成

		logger.Info("启动交易队列处理服务")

		for {
			// 处理交易队列
			handler.StartProcessTransactionQueue()
			// 添加处理间隔，防止过度消耗系统资源
		}
	}()

	logger.Info("交易队列处理服务已启动")
}
