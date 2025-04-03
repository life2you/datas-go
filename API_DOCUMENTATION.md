# Pump Data API 文档

本文档描述了 Pump Data API 的使用方法，这些 API 接口为前端应用提供代币数据访问服务。

## 基本信息

- 基础URL: `http://your-host:8000`
- 所有请求和响应均使用 JSON 格式
- 所有数据接口都支持分页

## 启动API服务器

```bash
# 默认配置启动（0.0.0.0:8000）
python run_api.py

# 指定主机和端口
python run_api.py --host 127.0.0.1 --port 8080
```

启动后，可以访问 `http://your-host:8000/docs` 查看交互式 API 文档（Swagger UI）。

## API 接口

### 1. 获取代币列表

获取代币列表，支持分页、排序和筛选。

- 请求方法: `GET`
- 路径: `/api/tokens`

**参数:**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|-------|------|
| page | int | 否 | 1 | 页码，从1开始 |
| limit | int | 否 | 20 | 每页数量，最大100 |
| sort | string | 否 | v_sol_in_bonding_curve | 排序字段 |
| order | string | 否 | desc | 排序方向(asc/desc) |
| name | string | 否 | - | 按名称筛选（模糊匹配） |
| symbol | string | 否 | - | 按符号筛选（模糊匹配） |
| min_sol | float | 否 | - | 最小SOL值 |
| max_sol | float | 否 | - | 最大SOL值 |

**排序字段:**

- `mint`: 代币地址
- `name`: 代币名称
- `symbol`: 代币符号
- `initial_buy`: 初始购买代币数量
- `v_tokens_in_bonding_curve`: 当前池子代币数量
- `v_sol_in_bonding_curve`: 当前池子SOL数量
- `created_at`: 记录创建时间

**示例请求:**

```
GET /api/tokens?page=1&limit=10&sort=v_sol_in_bonding_curve&order=desc&min_sol=10
```

**响应:**

```json
{
  "items": [
    {
      "mint": "8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump",
      "name": "RUINATION DAY",
      "symbol": "RD",
      "uri": "https://example.com/token.png",
      "initial_buy": 100.0,
      "v_tokens_in_bonding_curve": 1000.0,
      "v_sol_in_bonding_curve": 115.005359057,
      "created_at": "2023-12-01T12:34:56",
      "buy_count": 50,
      "sell_count": 10,
      "reply_count": 12
    },
    // ... 更多代币
  ],
  "total": 123,    // 总数据量
  "page": 1,       // 当前页码
  "limit": 10,     // 每页数量
  "pages": 13      // 总页数
}
```

### 2. 获取代币详情

获取单个代币的详细信息。

- 请求方法: `GET`
- 路径: `/api/tokens/{mint}`

**参数:**

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| mint | string | 是 | 代币地址 |

**示例请求:**

```
GET /api/tokens/8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump
```

**响应:**

```json
{
  "mint": "8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump",
  "name": "RUINATION DAY",
  "symbol": "RD",
  "uri": "https://example.com/token.png",
  "initial_buy": 100.0,
  "v_tokens_in_bonding_curve": 1000.0,
  "v_sol_in_bonding_curve": 115.005359057,
  "created_at": "2023-12-01T12:34:56",
  "description": "This is a sample token description",
  "creator": "8Kw7iv5iXBAwbrXLouvNjv1jWg4YZfT8cwaAp7xBTYeE",
  "creator_name": "User123",
  "max_supply": 1000000,
  "buy_count": 50,
  "sell_count": 10,
  "reply_count": 12
}
```

### 3. 获取代币回复列表

获取特定代币的回复列表，支持分页。

- 请求方法: `GET`
- 路径: `/api/tokens/{mint}/replies`

**参数:**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|-------|------|
| mint | string | 是 | - | 代币地址 |
| page | int | 否 | 1 | 页码，从1开始 |
| limit | int | 否 | 20 | 每页数量，最大100 |

**示例请求:**

```
GET /api/tokens/8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump/replies?page=1&limit=10
```

**响应:**

```json
{
  "items": [
    {
      "id": 123,
      "mint": "8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump",
      "is_buy": true,
      "sol_amount": 5.5,
      "user_address": "8Kw7iv5iXBAwbrXLouvNjv1jWg4YZfT8cwaAp7xBTYeE",
      "username": "User123",
      "timestamp": 1701401696000,
      "datetime": "2023-12-01T12:34:56",
      "text": "Great token!",
      "total_likes": 15
    },
    // ... 更多回复
  ],
  "total": 45,     // 总数据量
  "page": 1,       // 当前页码
  "limit": 10,     // 每页数量
  "pages": 5       // 总页数
}
```

### 4. 获取代币交易列表

获取特定代币的交易列表，支持分页和交易类型筛选。

- 请求方法: `GET`
- 路径: `/api/tokens/{mint}/trades`

**参数:**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|-------|------|
| mint | string | 是 | - | 代币地址 |
| page | int | 否 | 1 | 页码，从1开始 |
| limit | int | 否 | 20 | 每页数量，最大100 |
| type | string | 否 | all | 交易类型(buy/sell/all) |

**示例请求:**

```
GET /api/tokens/8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump/trades?page=1&limit=10&type=buy
```

**响应:**

```json
{
  "items": [
    {
      "id": 456,
      "mint": "8HtBDEiK3x6btQT5PQLXwGWKDfTTV1tecPR3JqZ9pump",
      "is_buy": true,
      "user_address": "8Kw7iv5iXBAwbrXLouvNjv1jWg4YZfT8cwaAp7xBTYeE",
      "username": "User123",
      "timestamp": 1701401696000,
      "datetime": "2023-12-01T12:34:56",
      "sol_amount": 2.5,
      "token_amount": 25.0,
      "tx_signature": "4gL9VTaDB6AvEU1QHaxENWyFWMqXEQLcBQ8eWrMtPXQ5p2D8kxLaX9nJjhRKwKBcPr3vp4MVaK6AwKyixcJzEhQa"
    },
    // ... 更多交易
  ],
  "total": 50,     // 总数据量
  "page": 1,       // 当前页码
  "limit": 10,     // 每页数量
  "pages": 5       // 总页数
}
```

## 错误处理

所有接口在发生错误时都会返回适当的HTTP状态码和JSON格式的错误信息。

**示例错误响应:**

```json
{
  "detail": "代币不存在"
}
```

常见HTTP状态码:

- 200: 请求成功
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

## 数据模型

### TokenBase (代币基本信息)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| mint | string | 代币地址 |
| name | string | 代币名称 |
| symbol | string | 代币符号 |
| uri | string | 代币头像URI |
| initial_buy | number | 初始购买代币数量 |
| v_tokens_in_bonding_curve | number | 当前池子代币数量 |
| v_sol_in_bonding_curve | number | 当前池子SOL数量 |
| created_at | string | 记录创建时间 |
| buy_count | number | 买入交易数量 |
| sell_count | number | 卖出交易数量 |
| reply_count | number | 回复总数 |

### TokenDetail (代币详细信息)

继承 TokenBase 的所有字段，并添加:

| 字段名 | 类型 | 描述 |
|--------|------|------|
| description | string | 代币描述 |
| creator | string | 创建者地址 |
| creator_name | string | 创建者名称 |
| max_supply | number | 最大供应量 |

### TokenReply (代币回复)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | number | 回复ID |
| mint | string | 代币地址 |
| is_buy | boolean | 是否买入 |
| sol_amount | number | SOL金额 |
| user_address | string | 用户地址 |
| username | string | 用户名 |
| timestamp | number | 时间戳(毫秒) |
| datetime | string | 时间 |
| text | string | 回复内容 |
| total_likes | number | 点赞数 |

### TokenTrade (代币交易)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | number | 交易ID |
| mint | string | 代币地址 |
| is_buy | boolean | 是否买入 |
| user_address | string | 用户地址 |
| username | string | 用户名 |
| timestamp | number | 时间戳(毫秒) |
| datetime | string | 时间 |
| sol_amount | number | SOL金额 |
| token_amount | number | 代币数量 |
| tx_signature | string | 交易签名 | 