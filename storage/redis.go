package storage

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/gagliardetto/solana-go/rpc"
	"github.com/redis/go-redis/v9"

	"github.com/life2you/datas-go/configs"
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
	// 交易签名队列
	TransactionQueueKey = "solana:transaction:queue"
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

// 队列操作方法

// PushToTransactionQueue 将交易签名推送到队列
// 参数:
//   - ctx: 上下文
//   - signatures: 交易签名列表
//
// 返回:
//   - error: 错误信息
func (r *RedisClient) PushToTransactionQueue(ctx context.Context, signatures []string) error {
	if len(signatures) == 0 {
		return nil
	}

	// 将字符串数组转换为接口数组
	args := make([]interface{}, len(signatures))
	for i, sig := range signatures {
		args[i] = sig
	}

	// 使用RPUSH将签名添加到队列末尾
	_, err := r.client.RPush(ctx, TransactionQueueKey, args...).Result()
	if err != nil {
		return fmt.Errorf("将交易签名推送到队列失败: %w", err)
	}

	return nil
}

// PopFromTransactionQueue 从队列中弹出指定数量的交易签名
// 参数:
//   - ctx: 上下文
//   - count: 要弹出的签名数量，如果为0则获取单个签名
//
// 返回:
//   - []string: 交易签名列表
//   - error: 错误信息
func (r *RedisClient) PopFromTransactionQueue(ctx context.Context, count int) ([]string, error) {
	if count <= 0 {
		count = 1
	}

	// 使用LPOP获取队列头部的元素（保证先进先出）
	if count == 1 {
		sig, err := r.client.LPop(ctx, TransactionQueueKey).Result()
		if err == redis.Nil {
			// 队列为空
			return nil, nil
		} else if err != nil {
			return nil, fmt.Errorf("从队列中获取交易签名失败: %w", err)
		}
		return []string{sig}, nil
	}

	// 使用LPOP命令多次获取多个元素
	pipe := r.client.Pipeline()
	for i := 0; i < count; i++ {
		pipe.LPop(ctx, TransactionQueueKey)
	}

	cmds, err := pipe.Exec(ctx)
	if err != nil {
		return nil, fmt.Errorf("从队列中批量获取交易签名失败: %w", err)
	}

	signatures := make([]string, 0, count)
	for _, cmd := range cmds {
		// 检查命令是否成功
		if cmd.Err() == redis.Nil {
			// 队列已经为空，退出循环
			break
		} else if cmd.Err() != nil {
			return signatures, fmt.Errorf("从队列中获取交易签名失败: %w", cmd.Err())
		}

		// 提取签名
		sig, err := cmd.(*redis.StringCmd).Result()
		if err != nil {
			continue
		}
		signatures = append(signatures, sig)
	}

	return signatures, nil
}

// GetTransactionQueueLength 获取交易签名队列长度
// 参数:
//   - ctx: 上下文
//
// 返回:
//   - int64: 队列长度
//   - error: 错误信息
func (r *RedisClient) GetTransactionQueueLength(ctx context.Context) (int64, error) {
	length, err := r.client.LLen(ctx, TransactionQueueKey).Result()
	if err != nil {
		return 0, fmt.Errorf("获取交易签名队列长度失败: %w", err)
	}
	return length, nil
}
