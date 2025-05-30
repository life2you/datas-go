package handler

import (
	"context"
	"encoding/json"
	"strings"
	"sync"
	"time"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/models"
	"github.com/life2you/datas-go/models/resp"
	"github.com/life2you/datas-go/rpc"
	"github.com/life2you/datas-go/storage"
	"go.uber.org/zap"
)

// 轮训扫描区块队列
func StartScanBlockQueue() {
	// 创建有超时控制的上下文
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	slotList := make([]uint64, 0)
	for {
		// 获取最小区块
		slotAny, _, ok := storage.GlobalBlockQueue.Pop()
		if !ok {
			break
		}
		slot := slotAny.(uint64)
		slotList = append(slotList, slot)
		if len(slotList) >= 3 {
			break
		}
	}

	if len(slotList) == 0 {
		logger.Info("没有区块需要处理")
		return
	}

	wg := sync.WaitGroup{}
	for _, slot := range slotList {
		wg.Add(1)
		time.Sleep(200 * time.Millisecond)
		go func(slot uint64) {
			defer wg.Done()
			handleBlock(ctx, slot)
		}(slot)
	}
	wg.Wait()
}

func handleBlock(ctx context.Context, slot uint64) {
	logger.Info("开始处理区块", zap.Uint64("slot", slot))
	// 如果报错，则重试
	var blockResp json.RawMessage
	i := 0
	for {
		if i > 5 {
			logger.Error("重试5次获取区块数据失败", zap.Uint64("slot", slot))
			return
		}
		innerBlockResp, err := rpc.GlobalHeliusClient.GetBlock(ctx, slot, nil)
		if err != nil {
			i++
			logger.Error("获取区块数据失败", zap.Uint64("slot", slot), zap.Error(err))
			time.Sleep(2 * time.Second)
			continue
		}
		if innerBlockResp == nil {
			i++
			logger.Info("获取区块失败", zap.Uint64("slot", slot))
			time.Sleep(2 * time.Second)
			continue
		}
		if innerBlockResp != nil && len(innerBlockResp) > 0 {
			blockResp = innerBlockResp
			break
		}

		i++
	}
	// 解析区块
	var blockData resp.BlockResp
	err := json.Unmarshal(blockResp, &blockData)
	if err != nil {
		logger.Error("解析区块数据失败", zap.Uint64("slot", slot), zap.Error(err))
		return
	}

	logger.Info("获取区块成功", zap.Uint64("slot", slot))

	// 收集签名
	trans := make([]resp.Transactions, 0)
	for _, transaction := range blockData.Transactions {
		vote := false
		if transaction.Meta.LogMessages != nil && len(transaction.Meta.LogMessages) > 0 {
			for _, logMessage := range transaction.Meta.LogMessages {
				if strings.Contains(logMessage, "Vote111111111111111111111111111111111111111") {
					vote = true
					break
				}
			}
		}
		if vote {
			continue
		}
		if transaction.Meta.Status.Err.InstructionError != nil && len(transaction.Meta.Status.Err.InstructionError) > 0 {
			continue
		}
		trans = append(trans, transaction)
	}

	signatures := make([]string, 0)
	for _, transaction := range trans {
		signatures = append(signatures, transaction.Transaction.Signatures...)
	}

	// 将签名存入Redis队列，使用区块高度进行分组
	if len(signatures) > 0 {
		// if err := storage.GlobalRedisClient.PushTransactionsForBlock(ctx, slot, signatures); err != nil {
		// 	logger.Error("将交易签名推送到队列失败", zap.Error(err), zap.Uint64("slot", slot))
		// 	return
		// }
		transactionQueueModel := models.TransactionQueueModel{
			Signatures: signatures,
			Slot:       slot,
		}
		storage.GlobalTransactionQueue.Push(transactionQueueModel, int64(slot))
		logger.Info("交易签名已推送到区块队列", zap.Int("交易数", len(signatures)), zap.Uint64("slot", slot))
	} else {
		logger.Info("没有有效交易需要解析", zap.Uint64("slot", slot))
	}

	logger.Info("区块处理完成", zap.Uint64("slot", slot))

}
