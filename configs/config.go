package configs

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/spf13/viper"
)

// Config 包含应用程序的所有配置
type Config struct {
	App               AppConfig               `mapstructure:"app"`
	Log               LogConfig               `mapstructure:"log"`
	Proxy             ProxyConfig             `mapstructure:"proxy"`
	Redis             RedisConfig             `mapstructure:"redis"`
	WebSocket         WebSocketConfig         `mapstructure:"websocket"`
	HeliusAPI         HeliusAPIConfig         `mapstructure:"helius_api"`
	HeliusEnhancedAPI HeliusEnhancedAPIConfig `mapstructure:"helius_enhanced_api"`
}

// AppConfig 应用基本配置
type AppConfig struct {
	Name        string `mapstructure:"name"`
	Environment string `mapstructure:"environment"`
	Version     string `mapstructure:"version"`
}

// LogConfig 日志配置
type LogConfig struct {
	Level      string `mapstructure:"level"`       // 日志级别：debug, info, warn, error
	Format     string `mapstructure:"format"`      // 日志格式：json, console
	Path       string `mapstructure:"path"`        // 日志文件路径
	MaxSize    int    `mapstructure:"max_size"`    // 单个日志文件最大大小(MB)
	MaxBackups int    `mapstructure:"max_backups"` // 最大保留日志文件数
	MaxAge     int    `mapstructure:"max_age"`     // 日志文件保留天数
	Compress   bool   `mapstructure:"compress"`    // 是否压缩
	Stdout     bool   `mapstructure:"stdout"`      // 是否输出到控制台
}

// RedisConfig Redis配置
type RedisConfig struct {
	Addr     string        `mapstructure:"addr"`
	Password string        `mapstructure:"password"`
	DB       int           `mapstructure:"db"`
	PoolSize int           `mapstructure:"pool_size"`
	Timeout  time.Duration `mapstructure:"timeout"`
}

// WebSocketConfig WebSocket客户端配置
type WebSocketConfig struct {
	Enabled           bool          `mapstructure:"enabled"`            // 是否启用WebSocket
	NetworkType       string        `mapstructure:"network_type"`       // 网络类型：mainnet, devnet
	APIKey            string        `mapstructure:"api_key"`            // Helius API密钥
	ReconnectInterval time.Duration `mapstructure:"reconnect_interval"` // 重连间隔
	ProxyURL          string        `mapstructure:"proxy_url"`          // 代理服务器URL
	OnConnect         func()        // 连接建立时的回调函数
}

// HeliusAPIConfig Helius API配置
type HeliusAPIConfig struct {
	APIKey   string `mapstructure:"api_key"`   // Helius API密钥
	Endpoint string `mapstructure:"endpoint"`  // Helius API端点
	ProxyURL string `mapstructure:"proxy_url"` // 代理服务器URL
}

type HeliusEnhancedAPIConfig struct {
	APIKeys  []string `mapstructure:"api_keys"`  // 多个Helius API密钥
	Endpoint string   `mapstructure:"endpoint"`  // Helius API端点
	ProxyURL string   `mapstructure:"proxy_url"` // 代理服务器URL
}

// ProxyConfig 代理配置
type ProxyConfig struct {
	Enabled bool   `mapstructure:"enabled"` // 是否启用代理
	URL     string `mapstructure:"url"`     // 代理服务器URL
}

// 全局配置实例
var GlobalConfig *Config

// LoadConfig 加载配置文件
func LoadConfig(configPath string) {
	v := viper.New()

	// 设置默认配置
	setDefaultConfig(v)

	// 根据path确定配置文件路径
	if configPath == "" {
		// 默认按以下顺序查找配置文件：
		// 1. 当前目录
		// 2. $HOME/.config/datas-go
		// 3. /etc/datas-go
		v.AddConfigPath(".")
		v.AddConfigPath("$HOME/.config/datas-go")
		v.AddConfigPath("/etc/datas-go")
		v.SetConfigName("config")
	} else {
		// 如果提供了配置文件路径
		dir, file := filepath.Split(configPath)
		ext := filepath.Ext(file)
		if dir != "" {
			v.AddConfigPath(dir)
		} else {
			v.AddConfigPath(".")
		}

		if ext != "" {
			v.SetConfigType(strings.TrimPrefix(ext, "."))
			v.SetConfigName(strings.TrimSuffix(file, ext))
		} else {
			v.SetConfigName(file)
		}
	}

	// 支持从环境变量读取配置，环境变量前缀为DATAS_GO
	v.SetEnvPrefix("DATAS_GO")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_"))
	v.AutomaticEnv()

	// 读取配置文件
	if err := v.ReadInConfig(); err != nil {
		// 如果找不到配置文件，创建默认配置文件
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			panic(fmt.Errorf("找不到指定的配置文件: %s, 错误: %w", configPath, err))
		} else {
			panic(fmt.Errorf("读取配置文件失败: %w", err))
		}
	}

	// 解析配置
	cfg := &Config{}
	if err := v.Unmarshal(cfg); err != nil {
		panic(fmt.Errorf("解析配置失败: %w", err))
	}

	// 设置全局配置
	GlobalConfig = cfg
}

// setDefaultConfig 设置默认配置
func setDefaultConfig(v *viper.Viper) {
	// 应用配置
	v.SetDefault("app.name", "datas-go")
	v.SetDefault("app.environment", "development")
	v.SetDefault("app.version", "0.1.0")

	// 日志配置
	v.SetDefault("log.level", "info")
	v.SetDefault("log.format", "console")
	v.SetDefault("log.path", "logs/datas-go.log")
	v.SetDefault("log.max_size", 100)
	v.SetDefault("log.max_backups", 3)
	v.SetDefault("log.max_age", 7)
	v.SetDefault("log.compress", true)
	v.SetDefault("log.stdout", true)

	// RPC配置
	v.SetDefault("rpc.endpoint", "https://api.mainnet-beta.solana.com")
	v.SetDefault("rpc.proxy_url", "")
	v.SetDefault("rpc.timeout", 30*time.Second)
	v.SetDefault("rpc.custom_headers", map[string]string{})
	v.SetDefault("rpc.retries", 3)
	v.SetDefault("rpc.retry_interval", 1*time.Second)

	// Redis配置
	v.SetDefault("redis.addr", "localhost:6379")
	v.SetDefault("redis.password", "")
	v.SetDefault("redis.db", 0)
	v.SetDefault("redis.pool_size", 10)
	v.SetDefault("redis.timeout", 5*time.Second)

	// 解析器配置
	v.SetDefault("parser.poll_interval", 1*time.Second)
	v.SetDefault("parser.batch_size", 100)
	v.SetDefault("parser.state_file_path", "./data/last_slot.dat")
	v.SetDefault("parser.concurrent_workers", 5)

	// WebSocket配置
	v.SetDefault("websocket.enabled", false)
	v.SetDefault("websocket.network_type", "mainnet")
	v.SetDefault("websocket.api_key", "")
	v.SetDefault("websocket.reconnect_interval", 5*time.Second)
	v.SetDefault("websocket.proxy_url", "")
}

// createDefaultConfigFile 创建默认配置文件
func createDefaultConfigFile(path string) error {
	// 确保目录存在
	dir := filepath.Dir(path)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("创建配置目录失败: %w", err)
		}
	}

	// 默认配置文件内容
	defaultConfig := `# Solana区块解析器配置文件

# 应用基本配置
app:
  name: datas-go
  environment: development # 环境: development, production
  version: 0.1.0

# 日志配置
log:
  level: info          # 日志级别: debug, info, warn, error
  format: console      # 日志格式: json, console
  path: logs/datas-go.log  # 日志文件路径
  max_size: 100        # 单个日志文件最大大小(MB)
  max_backups: 3       # 最大保留日志文件数
  max_age: 7           # 日志文件保留天数
  compress: true       # 是否压缩
  stdout: true         # 是否输出到控制台

# 代理配置
proxy:
  # 是否启用代理
  enabled: false
  # 代理服务器URL，例如: http://proxy.example.com:8080
  url: ""

# Redis配置
redis:
  addr: localhost:6379  # Redis服务器地址
  password: ""          # Redis密码
  db: 0                 # 使用的数据库编号
  pool_size: 10         # 连接池大小
  timeout: 5s           # 连接超时时间
  
# WebSocket客户端配置
websocket:
  enabled: false         # 是否启用WebSocket
  network_type: mainnet  # 网络类型: mainnet, devnet
  api_key: ""            # Helius API密钥
  reconnect_interval: 5s # 重连间隔
  proxy_url: ""          # 代理服务器URL
`

	// 写入配置文件
	if err := os.WriteFile(path, []byte(defaultConfig), 0644); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}

	return nil
}
