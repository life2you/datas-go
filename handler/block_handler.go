package handler

import (
	"context"
	"encoding/json"
	"strings"
	"time"

	"github.com/life2you/datas-go/logger"
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

	// 获取最小区块
	slot, err := storage.GlobalRedisClient.GetMinBlock(ctx)
	if err != nil {
		logger.Error("获取最小区块失败", zap.Error(err))
		return
	}

	logger.Infof("-----[区块数据]---------->>>开始处理区块 %d<<<---------------", slot)
	blockResp, err := rpc.GlobalHeliusClient.GetBlock(ctx, slot, nil)
	if err != nil {
		logger.Error("获取区块数据失败", zap.Uint64("slot", slot), zap.Error(err))
		return
	}

	if blockResp == nil {
		logger.Info("获取区块失败", zap.Uint64("slot", slot))
		return
	}

	// 解析区块
	var blockData resp.BlockResp
	err = json.Unmarshal(blockResp, &blockData)
	if err != nil {
		logger.Error("解析区块数据失败", zap.Uint64("slot", slot), zap.Error(err))
		return
	}

	logger.Infof("-----[区块数据]---------->>>获取区块交易记录,区块高度：%d<<<---------------", slot)

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

	// 将签名存入Redis队列，而不是直接解析
	if len(signatures) > 0 {
		if err := storage.GlobalRedisClient.PushToTransactionQueue(ctx, signatures); err != nil {
			logger.Error("将交易签名推送到队列失败", zap.Error(err), zap.Uint64("slot", slot))
			return
		}
		logger.Infof("-----[区块数据]---------->>>交易签名已推送到队列,交易数：%d,区块高度：%d<<<---------------", len(signatures), slot)
	} else {
		logger.Infof("-----[区块数据]---------->>>没有有效交易需要解析,区块高度：%d<<<---------------", slot)
	}

	logger.Infof("-----[区块数据]---------->>>区块处理完成,区块高度：%d<<<---------------", slot)
}
