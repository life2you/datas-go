# 代币元数据功能说明

本文档介绍了代币元数据的获取、存储和API访问功能。

## 功能概述

系统会自动扫描token表中尚未处理元数据的代币记录，从URI获取元数据，并存储到数据库。主要功能包括：

1. 自动定时扫描代币元数据
2. 提供元数据的API访问接口
3. 支持查看元数据统计信息
4. 集成到代币详情中展示元数据

## 数据结构

### 1. 表结构

系统添加了一个新的`token_metadata`表，并在`token`表中增加了`has_meta_data`字段：

```sql
-- 添加has_meta_data字段到现有的token表
ALTER TABLE token ADD COLUMN has_meta_data SMALLINT DEFAULT 0;

-- 创建token_metadata表
CREATE TABLE token_metadata (
    id SERIAL PRIMARY KEY,
    mint VARCHAR(44) NOT NULL UNIQUE,
    description TEXT,
    image VARCHAR(255),
    twitter VARCHAR(255),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mint FOREIGN KEY (mint) REFERENCES token(mint) ON DELETE CASCADE
);

-- 创建索引提高查询性能
CREATE INDEX idx_token_metadata_mint ON token_metadata(mint);
```

### 2. 元数据状态标记

`token`表中的`has_meta_data`字段用于标记元数据处理状态：

- `0`: 尚未处理（初始值）
- `1`: 已成功处理
- `-1`: 无URI，无法处理
- `-2`: 请求失败或格式错误
- `-3`: 处理异常或保存失败

## 使用方法

### 1. 安装设置

1. 执行SQL脚本创建表结构：
   ```bash
   psql -d your_database_name -f sql/token_metadata.sql
   ```

2. 确保项目依赖已安装：
   ```bash
   pip install -r requirements.txt
   ```

### 2. 启动服务

启动API服务时会自动启动元数据扫描器：

```bash
python run_api.py
```

### 3. API接口

#### 获取代币元数据

```
GET /api/tokens/{mint}/metadata
```

**响应示例**：
```json
{
  "mint": "AbCdEf123456...",
  "description": "这是一个示例代币描述",
  "image": "https://ipfs.io/ipfs/QmXYZ...",
  "twitter": "https://twitter.com/example",
  "website": "https://example.com",
  "created_at": "2023-01-01T12:00:00",
  "updated_at": "2023-01-01T13:00:00"
}
```

#### 获取元数据统计信息

```
GET /api/metadata/stats
```

**响应示例**：
```json
{
  "total_tokens": 1000,
  "processed_tokens": 750,
  "pending_tokens": 200,
  "failed_tokens": 50,
  "metadata_count": 750,
  "scan_time": "2023-01-01T14:00:00"
}
```

#### 获取包含元数据的代币详情

```
GET /api/tokens/{mint}
```

**响应示例**：
```json
{
  "mint": "AbCdEf123456...",
  "name": "Example Token",
  "symbol": "EXT",
  "uri": "https://ipfs.io/ipfs/QmABC...",
  "initial_buy": 100.0,
  "v_tokens_in_bonding_curve": 1000.0,
  "v_sol_in_bonding_curve": 50.0,
  "created_at": "2023-01-01T12:00:00",
  "buy_count": 50,
  "sell_count": 20,
  "reply_count": 30,
  "description": "这是一个示例代币描述",
  "image": "https://ipfs.io/ipfs/QmXYZ...",
  "twitter": "https://twitter.com/example",
  "website": "https://example.com",
  "has_metadata": true
}
```

## 元数据扫描流程

1. 扫描器每3分钟触发一次扫描
2. 每次扫描最多处理100条记录
3. 对于每条记录：
   - 获取URI并发送HTTP请求
   - 解析返回的JSON数据
   - 提取需要的字段并保存到数据库
   - 更新处理状态

## 注意事项

1. IPFS链接自动处理：系统会自动将`ipfs://`协议转换为HTTP网关URL
2. 错误处理：对于请求失败的记录，系统会标记状态并记录日志
3. 并发限制：每次扫描限制处理的记录数，避免资源占用过高
4. 重复数据处理：使用`ON CONFLICT`子句确保不会插入重复记录 