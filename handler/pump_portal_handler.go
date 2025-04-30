package handler

import (
	"encoding/json"

	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/models/resp"
	"go.uber.org/zap"
)

func PumpPortalHandler(message json.RawMessage) {
	//logger.Info("PumpPortalHandler", zap.String("message", string(message)))
	var msg resp.ClassifyType
	err := json.Unmarshal(message, &msg)
	if err != nil {
		logger.Error("PumpPortalHandler", zap.String("error", err.Error()))
		return
	}
	if msg.TxType == "" {
		return
	}
	switch msg.TxType {
	case resp.Create:
	//logger.Info("create", zap.String("message", string(message)))
	case resp.Migrate:

	default:
		logger.Info(string(msg.TxType), zap.String("message", string(message)))
	}
}
