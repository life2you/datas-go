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
	// 获取API客户端数量
	clientCount := rpc.GetEnhancedApiClientCount()
	if clientCount == 0 {
		logger.Error("没有可用的API客户端")
		return
	}
	transactionItem, err := storage.GlobalRedisClient.LPopTransactionQueue(ctx)
	if err != nil {
		logger.Error("从队列获取交易批次失败", zap.Error(err))
		return
	}
	if transactionItem == nil {
		logger.Debug("队列已空，结束处理")
		return
	}
	signatures := slices.Chunk(transactionItem.Signatures, 50)
	var wg sync.WaitGroup
	var i = 0
	for signature := range signatures {
		clientIndex := i % clientCount
		time.Sleep(200 * time.Millisecond)
		wg.Add(1)
		go func(clientIndex int, signature []string) {
			defer wg.Done()
			processTransactionBatch(ctx, clientIndex, transactionItem.BlockSlot, signature...)
		}(clientIndex, signature)
		i++

	}
	// 等待所有处理完成
	wg.Wait()
	logger.Info("交易数据解析完成，区块  ",
		zap.Any("solana_slot", transactionItem.BlockSlot))
}

// 并行处理交易数据
func processTransactionBatch(ctx context.Context, clientIndex int, blockSlot uint64, signatures ...string) {
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
			zap.Uint64("区块", blockSlot),
			zap.Error(err))
		return
	}

	if len(transactionResp) == 0 {
		logger.Warn("交易响应为空",
			zap.Int("clientIndex", clientIndex),
			zap.Uint64("区块", blockSlot))
		return
	}

	// 解析交易响应
	var parsedTransactions []resp.ParsedTransaction
	if err := json.Unmarshal(transactionResp, &parsedTransactions); err != nil {
		logger.Error("解析交易数据失败",
			zap.Int("clientIndex", clientIndex),
			zap.Uint64("区块", blockSlot),
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
