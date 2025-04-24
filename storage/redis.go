package storage

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/gagliardetto/solana-go/rpc"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/life2you/datas-go/configs"
	"github.com/life2you/datas-go/logger"
)

const (
	// 区块有序集合的键名
	BlocksZSetKey = "solana:blocks:sorted"
	// 区块详情Hash表的前缀
	BlockHashPrefix = "solana:block:"
	// 区块数据过期时间(30天)
	BlockExpiration = 30 * 24 * time.Hour
	// 默认扫描批次大小
	DefaultScanCount = 100
	// 交易签名队列前缀 (按区块划分)
	TransactionQueueKeyPrefix = "solana:transaction:queue"
	// 区块处理记录集合
	ProcessedBlocksKey = "solana:blocks:processed"
)

// 定义常见错误
var (
	ErrBlockNotFound     = errors.New("找不到指定区块")
	ErrNoBlocksAvailable = errors.New("没有可用的区块")
	ErrRedisConnection   = errors.New("Redis连接失败")
)

// RedisOptions 定义Redis连接选项
type RedisOptions struct {
	Addr     string // Redis服务器地址，格式为"host:port"
	Password string // Redis密码，如无设置为""
	DB       int    // Redis数据库索引
	PoolSize int    // 连接池大小
}

var (
	GlobalRedisClient *RedisClient
)

// RedisClient 包装Redis客户端
type RedisClient struct {
	client *redis.Client
}

func (r *RedisClient) GetClient() *redis.Client {
	return r.client
}

// NewRedisClient 创建新的Redis客户端
func NewRedisClient(options *configs.RedisConfig) {
	client := redis.NewClient(&redis.Options{
		Addr:     options.Addr,
		Password: options.Password,
		DB:       options.DB,
		PoolSize: options.PoolSize,
	})

	// 测试连接
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := client.Ping(ctx).Result()
	if err != nil {
		panic(fmt.Errorf("%w: %v", ErrRedisConnection, err))
	}

	GlobalRedisClient = &RedisClient{
		client: client,
	}
}

// Close 关闭Redis连接
func (r *RedisClient) Close() error {
	return r.client.Close()
}

// StoreBlock 存储区块数据到Redis
// 参数:
//   - ctx: 上下文
//   - slot: 区块高度/槽位
//   - block: 区块数据
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) StoreBlock(ctx context.Context, slot uint64) error {

	// 使用管道执行多个命令以提高性能
	pipe := r.client.Pipeline()

	// 1. 将区块高度添加到有序集合，score为区块高度
	pipe.ZAdd(ctx, BlocksZSetKey, redis.Z{
		Score:  float64(slot),
		Member: slot,
	})
	// 执行管道命令
	_, err := pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("存储区块数据失败: %w", err)
	}
	return nil
}

// GetBlockBySlot 根据区块高度获取区块
// 参数:
//   - ctx: 上下文
//   - slot: 区块高度/槽位
//
// 返回:
//   - *rpc.GetBlockResult: 区块数据
//   - error: 错误信息
func (r *RedisClient) GetBlockBySlot(ctx context.Context, slot uint64) (*rpc.GetBlockResult, error) {
	// 构建区块详情的键
	blockKey := fmt.Sprintf("%s%d", BlockHashPrefix, slot)

	// 从Redis获取区块数据
	blockJSON, err := r.client.Get(ctx, blockKey).Result()
	if err == redis.Nil {
		return nil, ErrBlockNotFound
	} else if err != nil {
		return nil, fmt.Errorf("获取区块数据失败: %w", err)
	}

	// 反序列化区块数据
	var block rpc.GetBlockResult
	if err := json.Unmarshal([]byte(blockJSON), &block); err != nil {
		return nil, fmt.Errorf("解析区块数据失败: %w", err)
	}

	return &block, nil
}

// GetMinBlock 获取最小高度的区块 并移除
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - uint64: 区块高度
//   - error: 错误信息
func (r *RedisClient) GetMinBlock(ctx context.Context) (uint64, error) {
	// 使用ZRANGE获取最小score的元素(即最小区块高度)
	slots, err := r.client.ZRange(ctx, BlocksZSetKey, 0, 0).Result()
	if err != nil {
		return 0, fmt.Errorf("获取最小区块高度失败: %w", err)
	}

	if len(slots) == 0 {
		return 0, ErrNoBlocksAvailable
	}

	// 解析区块高度
	var slot uint64
	if _, err := fmt.Sscanf(slots[0], "%d", &slot); err != nil {
		return 0, fmt.Errorf("解析区块高度失败: %w", err)
	}

	// 从有序集合中移除该区块
	// 使用原始字符串格式的成员进行删除，与添加时的格式保持一致
	_, err = r.client.ZRem(ctx, BlocksZSetKey, slots[0]).Result()
	if err != nil {
		return 0, fmt.Errorf("移除最小区块失败: %w", err)
	}
	return slot, nil
}

// GetMaxBlock 获取最大高度的区块
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - uint64: 区块高度
//   - *rpc.GetBlockResult: 区块数据
//   - error: 错误信息
func (r *RedisClient) GetMaxBlock(ctx context.Context) (uint64, *rpc.GetBlockResult, error) {
	// 使用ZRANGE获取最大score的元素(即最大区块高度)，使用ZREVRANGE获取倒序第一个元素
	slots, err := r.client.ZRevRange(ctx, BlocksZSetKey, 0, 0).Result()
	if err != nil {
		return 0, nil, fmt.Errorf("获取最大区块高度失败: %w", err)
	}

	if len(slots) == 0 {
		return 0, nil, ErrNoBlocksAvailable
	}

	// 解析区块高度
	var slot uint64
	if _, err := fmt.Sscanf(slots[0], "%d", &slot); err != nil {
		return 0, nil, fmt.Errorf("解析区块高度失败: %w", err)
	}

	// 获取该区块的详细信息
	block, err := r.GetBlockBySlot(ctx, slot)
	if err != nil {
		return slot, nil, err
	}

	return slot, block, nil
}

// RemoveBlock 从Redis中删除指定区块
// 参数:
//   - ctx: 上下文
//   - slot: 区块高度/槽位
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) RemoveBlock(ctx context.Context, slot uint64) error {
	// 区块详情的Hash键
	blockKey := fmt.Sprintf("%s%d", BlockHashPrefix, slot)

	// 使用管道执行多个命令
	pipe := r.client.Pipeline()

	// 1. 从有序集合中移除区块高度
	pipe.ZRem(ctx, BlocksZSetKey, slot)

	// 2. 删除区块详情
	pipe.Del(ctx, blockKey)

	// 执行管道命令
	_, err := pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("删除区块数据失败: %w", err)
	}

	return nil
}

// BlockExists 检查区块是否存在
// 参数:
//   - ctx: 上下文
//   - slot: 区块高度/槽位
//
// 返回:
//   - bool: 区块是否存在
//   - error: 错误信息
func (r *RedisClient) BlockExists(ctx context.Context, slot uint64) (bool, error) {
	// 检查区块是否存在于有序集合中
	exists, err := r.client.ZScore(ctx, BlocksZSetKey, fmt.Sprintf("%d", slot)).Result()
	if err == redis.Nil {
		return false, nil
	} else if err != nil {
		return false, fmt.Errorf("检查区块是否存在失败: %w", err)
	}

	return exists > 0, nil
}

// GetBlockCount 获取存储的区块数量
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - int64: 区块数量
//   - error: 错误信息
func (r *RedisClient) GetBlockCount(ctx context.Context) (int64, error) {
	count, err := r.client.ZCard(ctx, BlocksZSetKey).Result()
	if err != nil {
		return 0, fmt.Errorf("获取区块数量失败: %w", err)
	}
	return count, nil
}

// GetBlocksRange 获取指定范围内的区块高度
// 参数:
//   - ctx: 上下文
//   - start: 起始索引
//   - stop: 结束索引
//
// 返回:
//   - []uint64: 区块高度列表
//   - error: 错误信息
func (r *RedisClient) GetBlocksRange(ctx context.Context, start, stop int64) ([]uint64, error) {
	// 从有序集合中获取指定范围的元素
	slotsStr, err := r.client.ZRange(ctx, BlocksZSetKey, start, stop).Result()
	if err != nil {
		return nil, fmt.Errorf("获取区块范围失败: %w", err)
	}

	// 解析区块高度
	slots := make([]uint64, 0, len(slotsStr))
	for _, slotStr := range slotsStr {
		var slot uint64
		if _, err := fmt.Sscanf(slotStr, "%d", &slot); err != nil {
			return nil, fmt.Errorf("解析区块高度失败: %w", err)
		}
		slots = append(slots, slot)
	}

	return slots, nil
}

// ClearBlocks 清空所有区块数据
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) ClearBlocks(ctx context.Context) error {
	// 获取所有区块高度
	slots, err := r.client.ZRange(ctx, BlocksZSetKey, 0, -1).Result()
	if err != nil {
		return fmt.Errorf("获取所有区块高度失败: %w", err)
	}

	if len(slots) == 0 {
		return nil // 没有区块数据，直接返回
	}

	// 构建所有区块详情的键
	blockKeys := make([]string, 0, len(slots))
	for _, slot := range slots {
		blockKey := fmt.Sprintf("%s%s", BlockHashPrefix, slot)
		blockKeys = append(blockKeys, blockKey)
	}

	// 使用管道执行多个命令
	pipe := r.client.Pipeline()

	// 1. 删除有序集合
	pipe.Del(ctx, BlocksZSetKey)

	// 2. 删除所有区块详情
	if len(blockKeys) > 0 {
		pipe.Del(ctx, blockKeys...)
	}

	// 执行管道命令
	_, err = pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("清空区块数据失败: %w", err)
	}

	return nil
}

// 存储Hash到redis

// StoreHash 存储哈希值到Redis
// 参数:
//   - ctx: 上下文
//   - key: 哈希键名
//   - field: 哈希字段名
//   - value: 哈希值
//   - expiration: 过期时间，如果为0则不设置过期时间
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) StoreHash(ctx context.Context, key string, field string, value interface{}, expiration time.Duration) error {
	if r == nil || r.client == nil {
		return errors.New("Redis 客户端尚未初始化")
	}

	// 构建Redis键名
	redisKey := fmt.Sprintf("solana:hash:%s", key)

	// 使用管道执行多个命令以提高性能
	pipe := r.client.Pipeline()

	// 设置哈希字段值
	pipe.HSet(ctx, redisKey, field, value)

	// 如果指定了过期时间，则设置键的过期时间
	if expiration > 0 {
		pipe.Expire(ctx, redisKey, expiration)
	}

	// 执行管道命令
	_, err := pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("存储哈希值失败: %w", err)
	}
	return nil
}

// 交易签名队列相关操作

// TransactionItem 表示交易队列中的项目
type TransactionItem struct {
	BlockSlot  uint64   `json:"block_slot"`  // 所属区块高度
	Signatures []string `json:"signatures"`  // 交易签名
	CreateTime int64    `json:"create_time"` // 创建时间(Unix时间戳)
}

// 获取区块对应的队列键名
func getBlockQueueKey(blockSlot uint64) string {
	return fmt.Sprintf("%s", TransactionQueueKeyPrefix)
}

// PushTransactionsForBlock 将交易签名存入指定区块的队列
// 参数:
//   - ctx: 上下文
//   - blockSlot: 区块高度
//   - signatures: 交易签名列表
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) PushTransactionsForBlock(ctx context.Context, blockSlot uint64, signatures []string) error {
	if len(signatures) == 0 {
		return nil
	}

	// 获取区块对应的队列键名
	queueKey := getBlockQueueKey(blockSlot)

	// 将区块添加到处理记录
	_, err := r.client.SAdd(ctx, ProcessedBlocksKey, blockSlot).Result()
	if err != nil {
		return fmt.Errorf("添加区块处理记录失败: %w", err)
	}

	// 当前时间戳
	now := time.Now().Unix()

	// 使用管道执行多个命令
	pipe := r.client.Pipeline()

	// 准备交易项目并序列化
	item := TransactionItem{
		BlockSlot:  blockSlot,
		Signatures: signatures,
		CreateTime: now,
	}

	// 序列化为JSON
	itemJSON, err := json.Marshal(item)
	if err != nil {
		return fmt.Errorf("序列化交易项目失败: %w", err)
	}
	// 添加到队列
	pipe.RPush(ctx, queueKey, itemJSON)
	// 执行管道命令
	_, err = pipe.Exec(ctx)
	if err != nil {
		return fmt.Errorf("将交易签名推送到队列失败: %w", err)
	}

	return nil
}

// LPopTransactionQueue 从队列中获取一个区块交易批次
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - *TransactionItem: 交易项目，包含区块高度和交易签名
//   - error: 错误信息
func (r *RedisClient) LPopTransactionQueue(ctx context.Context) (*TransactionItem, error) {
	// 从队列中获取一个元素
	itemJSON, err := r.client.LPop(ctx, TransactionQueueKeyPrefix).Result()
	if err == redis.Nil {
		// 队列为空
		return nil, nil
	} else if err != nil {
		return nil, fmt.Errorf("从队列获取交易项目失败: %w", err)
	}

	// 反序列化交易项目
	var item TransactionItem
	if err := json.Unmarshal([]byte(itemJSON), &item); err != nil {
		return nil, fmt.Errorf("解析交易项目失败: %w", err)
	}

	return &item, nil
}

// GetTransactionsFromBlock 从指定区块的队列中获取交易项目
// 参数:
//   - ctx: 上下文
//   - blockSlot: 区块高度
//   - count: 要获取的项目数量
//
// 返回:
//   - []TransactionItem: 交易项目列表
//   - error: 错误信息
func (r *RedisClient) GetTransactionsFromBlock(ctx context.Context, blockSlot uint64, count int) ([]TransactionItem, error) {
	if count <= 0 {
		count = 1
	}

	// 获取区块对应的队列键名
	queueKey := getBlockQueueKey(blockSlot)

	// 检查队列是否存在
	exists, err := r.client.Exists(ctx, queueKey).Result()
	if err != nil {
		return nil, fmt.Errorf("检查队列存在失败: %w", err)
	}

	if exists == 0 {
		// 队列不存在
		return nil, nil
	}

	// 获取队列长度
	queueLen, err := r.client.LLen(ctx, queueKey).Result()
	if err != nil {
		return nil, fmt.Errorf("获取队列长度失败: %w", err)
	}

	if queueLen == 0 {
		// 队列为空
		return nil, nil
	}

	// 调整count，不超过队列长度
	if int64(count) > queueLen {
		count = int(queueLen)
	}

	// 使用管道执行多个LPOP命令
	pipe := r.client.Pipeline()
	for i := 0; i < count; i++ {
		pipe.LPop(ctx, queueKey)
	}

	// 执行管道命令
	cmds, err := pipe.Exec(ctx)
	if err != nil {
		return nil, fmt.Errorf("从队列获取交易项目失败: %w", err)
	}

	// 解析结果
	items := make([]TransactionItem, 0, count)
	for _, cmd := range cmds {
		// 检查命令是否成功
		if cmd.Err() == redis.Nil {
			// 队列已经为空，退出循环
			break
		} else if cmd.Err() != nil {
			return items, fmt.Errorf("从队列获取交易项目失败: %w", cmd.Err())
		}

		// 获取JSON字符串
		itemJSON, err := cmd.(*redis.StringCmd).Result()
		if err != nil {
			logger.Warn("获取交易项目结果失败", zap.Error(err))
			continue
		}

		// 反序列化
		var item TransactionItem
		if err := json.Unmarshal([]byte(itemJSON), &item); err != nil {
			logger.Warn("解析交易项目失败", zap.String("json", itemJSON), zap.Error(err))
			continue
		}

		items = append(items, item)
	}

	return items, nil
}

// GetTransactionQueueLength 获取交易队列长度
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - int64: 队列长度
//   - error: 错误信息
func (r *RedisClient) GetTransactionQueueLength(ctx context.Context) (int64, error) {
	length, err := r.client.LLen(ctx, TransactionQueueKeyPrefix).Result()
	if err != nil {
		return 0, fmt.Errorf("获取交易队列长度失败: %w", err)
	}
	return length, nil
}

// RemoveProcessedBlock 从已处理区块集合中移除指定区块
// 参数:
//   - ctx: 上下文
//   - blockSlot: 区块高度
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) RemoveProcessedBlock(ctx context.Context, blockSlot uint64) error {
	_, err := r.client.SRem(ctx, ProcessedBlocksKey, blockSlot).Result()
	if err != nil {
		return fmt.Errorf("从已处理区块集合移除区块失败: %w", err)
	}
	return nil
}

// 保持向下兼容的方法

// PushToTransactionQueue 将交易签名推送到队列 (向下兼容)
func (r *RedisClient) PushToTransactionQueue(ctx context.Context, signatures []string) error {
	// 使用一个默认区块高度
	return r.PushTransactionsForBlock(ctx, 0, signatures)
}

// PopFromTransactionQueue 从队列中弹出指定数量的交易签名 (向下兼容)
func (r *RedisClient) PopFromTransactionQueue(ctx context.Context, count int) ([]string, error) {
	var allSignatures []string

	// 尝试获取足够的交易批次，直到收集足够的签名或队列为空
	for len(allSignatures) < count {
		item, err := r.LPopTransactionQueue(ctx)
		if err != nil {
			return allSignatures, err
		}

		if item == nil {
			// 队列为空
			break
		}

		// 添加签名到结果集
		allSignatures = append(allSignatures, item.Signatures...)

		// 如果已经收集足够的签名，可以提前退出
		if len(allSignatures) >= count {
			break
		}
	}

	// 如果收集的签名超过请求的数量，只返回请求的数量
	if len(allSignatures) > count {
		return allSignatures[:count], nil
	}

	return allSignatures, nil
}
