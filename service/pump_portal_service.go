package service

import (
	"context"
	"time"

	"github.com/life2you/datas-go/rpc"
)

func StartPumpPortalService() {
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	rpc.GlobalPumpPortalClient.Connect(ctx)
	err := rpc.GlobalPumpPortalClient.SubscribeNewToken()
	if err != nil {
		panic(err)
	}
	err = rpc.GlobalPumpPortalClient.SubscribeAccountTrade(make([]string, 0))
	if err != nil {
		panic(err)
	}
	err = rpc.GlobalPumpPortalClient.SubscribeMigration()
	if err != nil {
		panic(err)
	}
	err = rpc.GlobalPumpPortalClient.SubscribeTokenTrade(make([]string, 0))
	if err != nil {
		panic(err)
	}
}
