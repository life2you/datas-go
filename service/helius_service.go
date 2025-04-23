package service

import (
	"context"

	"github.com/life2you/datas-go/handler"

	"github.com/life2you/datas-go/rpc"
)

func StartHeliusService() {
	rpcClient := rpc.GlobalWebSocketClient
	rpcClient.Connect(context.Background())
	rpcClient.BlockSubscribe("confirmed", handler.HeliusSlotHandler)
}
