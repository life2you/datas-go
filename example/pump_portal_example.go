package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/life2you/datas-go/rpc"
)

func main() {
	// 创建PumpPortal客户端
	options := rpc.DefaultPumpPortalOptions()
	// 如果需要使用代理，可以设置代理URL
	// options.ProxyURL = "http://your-proxy-url:port"
	client := rpc.NewPumpPortalClient(options)

	// 建立连接
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := client.Connect(ctx); err != nil {
		log.Fatalf("连接PumpPortal失败: %v", err)
	}
	defer client.Close()

	// 处理新代币创建事件
	newTokenHandler := func(data json.RawMessage) {
		var token map[string]interface{}
		if err := json.Unmarshal(data, &token); err != nil {
			log.Printf("解析新代币数据失败: %v", err)
			return
		}
		log.Printf("收到新代币创建事件: %+v", token)
	}

	// 处理代币交易事件
	tokenTradeHandler := func(data json.RawMessage) {
		var trade map[string]interface{}
		if err := json.Unmarshal(data, &trade); err != nil {
			log.Printf("解析代币交易数据失败: %v", err)
			return
		}
		log.Printf("收到代币交易事件: %+v", trade)
	}

	// 处理账户交易事件
	accountTradeHandler := func(data json.RawMessage) {
		var trade map[string]interface{}
		if err := json.Unmarshal(data, &trade); err != nil {
			log.Printf("解析账户交易数据失败: %v", err)
			return
		}
		log.Printf("收到账户交易事件: %+v", trade)
	}

	// 处理代币迁移事件
	migrationHandler := func(data json.RawMessage) {
		var migration map[string]interface{}
		if err := json.Unmarshal(data, &migration); err != nil {
			log.Printf("解析代币迁移数据失败: %v", err)
			return
		}
		log.Printf("收到代币迁移事件: %+v", migration)
	}

	// 订阅新代币创建
	if err := client.SubscribeNewToken(newTokenHandler); err != nil {
		log.Printf("订阅新代币创建失败: %v", err)
	} else {
		log.Println("已订阅新代币创建事件")
	}

	// 订阅特定代币的交易
	tokenAddresses := []string{"91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p"}
	if err := client.SubscribeTokenTrade(tokenAddresses, tokenTradeHandler); err != nil {
		log.Printf("订阅代币交易失败: %v", err)
	} else {
		log.Printf("已订阅代币 %v 的交易事件", tokenAddresses)
	}

	// 订阅特定账户的交易
	accountAddresses := []string{"AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV"}
	if err := client.SubscribeAccountTrade(accountAddresses, accountTradeHandler); err != nil {
		log.Printf("订阅账户交易失败: %v", err)
	} else {
		log.Printf("已订阅账户 %v 的交易事件", accountAddresses)
	}

	// 订阅代币迁移事件
	if err := client.SubscribeMigration(migrationHandler); err != nil {
		log.Printf("订阅代币迁移事件失败: %v", err)
	} else {
		log.Println("已订阅代币迁移事件")
	}

	// 等待中断信号退出
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	fmt.Println("正在关闭...")

	// 取消订阅
	if err := client.UnsubscribeNewToken(); err != nil {
		log.Printf("取消订阅新代币创建失败: %v", err)
	}
	if err := client.UnsubscribeTokenTrade(tokenAddresses); err != nil {
		log.Printf("取消订阅代币交易失败: %v", err)
	}
	if err := client.UnsubscribeAccountTrade(accountAddresses); err != nil {
		log.Printf("取消订阅账户交易失败: %v", err)
	}
}
