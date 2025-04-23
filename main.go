package main

import (
	"os"
	"os/signal"
	"syscall"

	"go.uber.org/zap"

	"github.com/life2you/datas-go/configs"
	"github.com/life2you/datas-go/logger"
	"github.com/life2you/datas-go/rpc"
	"github.com/life2you/datas-go/service"
	"github.com/life2you/datas-go/storage"
)

func main() {
	// 启动步骤
	// 1. 初始化配置
	configs.LoadConfig("")

	// 2. 初始化日志
	logger.Init(&configs.GlobalConfig.Log)

	// 3. 初始化redis
	storage.NewRedisClient(&configs.GlobalConfig.Redis)

	// 4. 定义RPC回调函数
	rpcCallBack := func() {
		logger.Info("WebSocket连接成功")
	}

	// 5. 配置WebSocket
	configs.GlobalConfig.WebSocket.OnConnect = rpcCallBack

	// 如果RPC配置中有代理URL，则使用它
	if configs.GlobalConfig.Proxy.Enabled && configs.GlobalConfig.Proxy.URL != "" {
		logger.Info("使用代理连接Helius", zap.String("proxy", configs.GlobalConfig.Proxy.URL))
		configs.GlobalConfig.WebSocket.ProxyURL = configs.GlobalConfig.Proxy.URL
	}

	// 6. 初始化WebSocket客户端
	rpc.NewWebSocketClientOptions(&configs.GlobalConfig.WebSocket)
	if rpc.GlobalWebSocketClient == nil {
		logger.Fatal("WebSocket客户端初始化失败")
	}
	logger.Info("WebSocket客户端初始化成功")
	// 启动服务前添加检查
	if configs.GlobalConfig.WebSocket.Enabled {
		// 启动服务
		service.StartHeliusService()
	}

	// 9. 阻止程序退出
	// 添加信号处理代码
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		logger.Info("接收到退出信号，程序即将关闭...")
		// 执行清理操作
		if rpc.GlobalWebSocketClient != nil {
			rpc.GlobalWebSocketClient.Close()
		}
		if storage.GlobalRedisClient != nil {
			storage.GlobalRedisClient.Close()
		}
		os.Exit(0)
	}()
}
