package service

import (
	"time"

	"github.com/life2you/datas-go/handler"
	"github.com/life2you/datas-go/logger"
)

func ScanBlockQueue() {
	go func() {
		for {
			// 处理一个区块
			handler.StartScanBlockQueue()

			// 添加延迟以避免过快处理
			logger.Debug("区块扫描完成，等待下一次扫描")
			time.Sleep(5 * time.Second)
		}
	}()
}
