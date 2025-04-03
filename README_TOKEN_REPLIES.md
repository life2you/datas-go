# 代币回复数据采集功能

本功能用于定期从Pump API获取高价值代币的回复数据，并存入数据库，供后续分析和处理。

## 功能特点

- 定期自动扫描数据库中SOL价值高于阈值的代币
- 获取这些代币的所有回复数据，包括交易信息、用户、内容等
- 支持增量更新，不会重复获取数据
- 可配置运行间隔、SOL阈值等参数

## 配置说明

在 `.env` 文件中可以配置以下参数：

```
# 代币回复数据采集配置
# 是否启用代币回复数据采集 (true/false)
TOKEN_REPLIES_ENABLED=true
# 数据采集间隔（秒），默认300秒（5分钟）
TOKEN_REPLIES_INTERVAL=300
# SOL阈值，只处理bonding curve中SOL大于此值的代币
TOKEN_REPLIES_SOL_THRESHOLD=35.0
# 每次获取回复的数量限制
TOKEN_REPLIES_FETCH_LIMIT=1000
# 可选的Cookie字符串，用于身份验证
TOKEN_REPLIES_COOKIE=
```

## 数据库表结构

数据存储在 `token_replies` 表中，字段如下：

```sql
CREATE TABLE IF NOT EXISTS token_replies (
    id SERIAL PRIMARY KEY,
    mint TEXT NOT NULL,
    is_buy BOOLEAN,
    sol_amount NUMERIC(20, 9),
    user_address TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    datetime TIMESTAMP,
    text TEXT,
    username TEXT,
    total_likes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mint, user_address, timestamp)
);
```

## 使用方法

### 随应用启动

代币回复数据采集功能默认随主应用一起启动。可以通过命令行参数 `--no-replies` 禁用此功能：

```bash
python run.py --no-replies
```

### 命令行参数

在 `main.py` 中支持以下与代币回复数据采集相关的命令行参数：

- `--no-replies`: 不启动代币回复数据采集服务
- `--config`: 显示当前配置信息，包括代币回复数据采集的配置

### 独立运行

可以单独运行数据采集脚本：

```bash
python fetch_pump_replies.py --once --sol 35.0
```

参数说明：
- `--once`: 只运行一次，不循环
- `--sol`: SOL阈值，只处理bonding curve中SOL大于此值的代币
- `--cookie`: 可选的Cookie字符串，用于身份验证
- `--proxy`: 是否使用代理
- `--interval`: 运行间隔（秒），只在循环模式下有效

## 实现细节

实现采用了异步编程模式，主要组件包括：

1. `TokenRepliesService`: 服务类，负责定期执行数据采集任务
2. `PumpDataProcessor`: 数据处理器，处理API数据并存入数据库
3. `PumpApiClient`: API客户端，负责与Pump API通信

服务启动后，会以配置的间隔时间定期扫描数据库中的高价值代币，获取这些代币的回复数据，并存入数据库。 