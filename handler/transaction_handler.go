package handler

import (
	"context"
	"encoding/json"
	"slices"
	"sync"
	"time"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/models/resp"
	"github.com/life2you/datas-go/rpc"
	"github.com/life2you/datas-go/storage"
	"go.uber.org/zap"
)

// 处理队列中的交易签名
func StartProcessTransactionQueue() {
	// 创建有超时控制的上下文
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// 获取队列长度
	queueLength, err := storage.GlobalRedisClient.GetTransactionQueueLength(ctx)
	if err != nil {
		logger.Error("获取队列长度失败", zap.Error(err))
		return
	}

	if queueLength == 0 {
		logger.Debug("交易队列为空，等待下一轮处理")
		return
	}

	logger.Infof("-----[交易数据]---------->>>开始处理交易队列,队列长度：%d<<<---------------", queueLength)

	// 获取API客户端数量
	clientCount := rpc.GetEnhancedApiClientCount()
	if clientCount == 0 {
		logger.Error("没有可用的API客户端")
		return
	}

	// 计算每个批次的大小，最大100条
	batchSize := 30
	if queueLength < int64(batchSize) {
		batchSize = int(queueLength)
	}

	// 计算要处理的批次数，但最多处理10个批次，防止一次处理太多
	batchCount := int(queueLength) / batchSize
	if batchCount > 10 {
		batchCount = 10
	}
	if batchCount == 0 {
		batchCount = 1
	}

	// 等待组用于同步所有goroutine
	var wg sync.WaitGroup

	// 为每个批次分配一个goroutine处理
	for i := 0; i < batchCount; i++ {
		// 从队列中获取一批交易签名
		signatures, err := storage.GlobalRedisClient.PopFromTransactionQueue(ctx, batchSize)
		if err != nil {
			logger.Error("从队列获取交易签名失败", zap.Error(err))
			continue
		}

		if len(signatures) == 0 {
			logger.Debug("队列已空，结束处理")
			break
		}

		// 计算这批签名应该分配给哪个客户端
		clientIndex := i % clientCount
		batchIndex := i

		time.Sleep(200 * time.Millisecond)
		// 添加到等待组
		wg.Add(1)
		// 启动goroutine处理这批交易
		go func(clientIndex, batchIndex int, sigs []string) {
			defer wg.Done()
			processTransactionBatch(ctx, clientIndex, batchIndex, sigs)
		}(clientIndex, batchIndex, signatures)
	}

	// 等待所有处理完成
	wg.Wait()

	// 获取处理后的队列长度
	remainingLength, _ := storage.GlobalRedisClient.GetTransactionQueueLength(ctx)
	logger.Infof("-----[交易数据]---------->>>交易队列处理完成,原队列长度：%d,剩余长度：%d<<<---------------", queueLength, remainingLength)
}

// 并行处理交易数据
func processTransactionBatch(ctx context.Context, clientIndex int, batchIndex int, signatures []string) {
	client := rpc.GetEnhancedApiClientByIndex(clientIndex)
	if client == nil {
		logger.Error("获取API客户端失败", zap.Int("clientIndex", clientIndex))
		return
	}

	// 创建批次专用上下文
	batchCtx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// 使用指定客户端解析交易
	transactionResp, err := client.ParseTransactions(batchCtx, signatures...)
	if err != nil {
		logger.Error("解析交易失败",
			zap.Int("clientIndex", clientIndex),
			zap.Int("batchIndex", batchIndex),
			zap.Error(err))
		return
	}

	if len(transactionResp) == 0 {
		logger.Warn("交易响应为空",
			zap.Int("clientIndex", clientIndex),
			zap.Int("batchIndex", batchIndex))
		return
	}

	// 解析交易响应
	var parsedTransactions []resp.ParsedTransaction
	if err := json.Unmarshal(transactionResp, &parsedTransactions); err != nil {
		logger.Error("解析交易数据失败",
			zap.Int("clientIndex", clientIndex),
			zap.Int("batchIndex", batchIndex),
			zap.Error(err))
		return
	}

	// 处理每个交易
	for _, transaction := range parsedTransactions {
		if transaction.TransactionError != nil &&
			transaction.TransactionError.InstructionError != nil &&
			len(transaction.TransactionError.InstructionError) > 0 {
			continue
		}

		if slices.Contains(resp.NeedToParseTransactionType, transaction.Type) {
			//logger.Info("交易", zap.Any("transaction", transaction))
			// 存储交易数据
			if err := storage.GlobalRedisClient.StoreHash(ctx, transaction.Source, transaction.Source, string(transaction.Type), 0); err != nil {
				logger.Error("存储交易哈希失败1", zap.Error(err))
			}
			err := storage.GlobalRedisClient.StoreHash(ctx, transaction.Source+"_"+string(transaction.Type), transaction.Signature, string(transaction.Type), 0)
			if err != nil {
				logger.Error("存储交易哈希失败2", zap.Error(err))
			}
		}
	}
}
