# datas-go

## 项目简介

这是一个用于连接PumpPortal WebSocket API的Python客户端，可以获取实时交易和代币创建数据，并存储到PostgreSQL数据库中。通过这个客户端，您可以订阅以下类型的实时数据：

- 新代币创建事件
- 迁移事件
- 账户交易事件
- 代币交易事件

## 项目结构

```
datas-go/
├── src/                    # 源代码目录
│   ├── api/                # API接口模块
│   ├── config/             # 配置文件
│   ├── db/                 # 数据库相关模块
│   ├── models/             # 数据模型
│   ├── utils/              # 工具函数
│   ├── main.py             # 主程序入口
│   └── pump_portal_client.py # WebSocket客户端
├── venv/                   # 虚拟环境
├── .env                    # 环境变量配置
├── init.py                 # 初始化脚本
├── requirements.txt        # 项目依赖
├── run.py                  # 主启动脚本
├── run_api.py              # API服务器启动脚本
├── table.sql               # 数据库表结构
├── API_DOCUMENTATION.md    # API文档
└── README.md               # 项目说明
```

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/datas-go.git
cd datas-go
```

2. 运行初始化脚本：

```bash
python init.py
```

初始化脚本会自动完成以下工作：
- 创建虚拟环境并安装依赖
- 初始化数据库表结构

如果需要跳过某些步骤，可以使用参数：
- `--skip-venv`：跳过虚拟环境设置
- `--skip-db`：跳过数据库初始化

## 配置

编辑`.env`文件设置环境变量：

```
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pumpportal
DB_USER=postgres
DB_PASSWORD=postgres

# WebSocket API配置
WEBSOCKET_URI=wss://pumpportal.fun/api/data

# 日志配置
LOG_LEVEL=INFO

# 其他配置
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# 事件监听配置
# 是否监听新代币创建事件 (true/false)
LISTEN_NEW_TOKEN=true
# 是否监听迁移事件 (true/false)
LISTEN_MIGRATION=true
# 是否启用静默模式，不在控制台打印事件数据 (true/false)
QUIET_MODE=false
# 要监控的账户地址列表，用逗号分隔
WATCH_ACCOUNTS=AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV
# 要监控的代币地址列表，用逗号分隔
WATCH_TOKENS=91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p
```

### 事件监听配置说明

您可以通过修改`.env`文件中的以下设置来配置要监听的事件：

- `LISTEN_NEW_TOKEN`：设置为`true`或`false`，控制是否监听新代币创建事件
- `LISTEN_MIGRATION`：设置为`true`或`false`，控制是否监听迁移事件
- `QUIET_MODE`：设置为`true`或`false`，控制是否在控制台显示接收到的事件数据
- `WATCH_ACCOUNTS`：要监听的账户地址列表，多个地址用逗号分隔
- `WATCH_TOKENS`：要监听的代币地址列表，多个地址用逗号分隔

## 数据库设置

1. 确保PostgreSQL服务器已安装并启动
2. 创建数据库：

```bash
createdb pumpportal
```

3. 初始化数据库表结构：

```bash
python -m src.db.init_db
```

## 使用方法

### 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 运行主程序
python -m src.main
```

### 查看当前配置

要查看当前从配置文件加载的设置：

```bash
python -m src.main --config
```

### 命令行参数

```bash
python -m src.main --help
```

可用参数（这些参数会覆盖配置文件中的设置）：
- `--accounts`：指定要监控的账户地址列表
- `--tokens`：指定要监控的代币地址列表
- `--no-new-token`：不订阅新代币创建事件
- `--no-migration`：不订阅迁移事件
- `--quiet`：不在控制台打印事件数据
- `--config`：显示当前配置信息并退出

示例：

```bash
# 监控特定账户和代币（覆盖配置文件中的设置）
python -m src.main --accounts AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV --tokens 91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p

# 静默模式，只存储数据不打印
python -m src.main --quiet
```

## 使用API服务

该项目提供了一个基于FastAPI的REST API服务，用于前端应用访问代币数据。

### 启动API服务器

```bash
# 使用默认配置（监听 0.0.0.0:8000）
python run_api.py

# 自定义主机和端口
python run_api.py --host 127.0.0.1 --port 8080
```

### API文档

启动API服务器后，可以访问以下URL查看交互式API文档：

- Swagger UI: `http://your-host:8000/docs`
- ReDoc: `http://your-host:8000/redoc`

### 主要API接口

API服务提供以下主要接口：

1. **代币列表** - `GET /api/tokens`
   - 获取所有代币的列表，支持分页、排序和筛选

2. **代币详情** - `GET /api/tokens/{mint}`
   - 获取特定代币的详细信息

3. **代币回复列表** - `GET /api/tokens/{mint}/replies`
   - 获取特定代币的所有回复，支持分页

4. **代币交易列表** - `GET /api/tokens/{mint}/trades`
   - 获取特定代币的所有交易，支持分页和交易类型筛选

完整的API文档请参考 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)。

## 数据库表结构

数据存储在`token_events`表中，表结构如下：

```sql
CREATE TABLE token_events (
    id SERIAL PRIMARY KEY,
    signature TEXT NOT NULL,
    mint TEXT NOT NULL,
    trader_public_key TEXT NOT NULL,
    tx_type TEXT NOT NULL,
    initial_buy NUMERIC(20, 6),
    sol_amount NUMERIC(20, 9),
    bonding_curve_key TEXT,
    v_tokens_in_bonding_curve NUMERIC(20, 6),
    v_sol_in_bonding_curve NUMERIC(20, 9),
    market_cap_sol NUMERIC(20, 9),
    name TEXT,
    symbol TEXT,
    uri TEXT,
    pool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API 参考

### PumpPortalClient 类

主要的客户端类，用于连接WebSocket服务器并处理消息。

#### 方法

- `connect()` - 连接到WebSocket服务器
- `disconnect()` - 断开与WebSocket服务器的连接
- `subscribe_new_token()` - 订阅新代币创建事件
- `subscribe_migration()` - 订阅迁移事件
- `subscribe_account_trade(accounts)` - 订阅账户交易事件
- `subscribe_token_trade(tokens)` - 订阅代币交易事件
- `unsubscribe_new_token()` - 取消订阅新代币创建事件
- `unsubscribe_account_trade()` - 取消订阅账户交易事件
- `unsubscribe_token_trade()` - 取消订阅代币交易事件
- `listen()` - 开始监听消息

#### 事件处理

- `on_new_token(callback)` - 注册新代币创建事件回调
- `on_migration(callback)` - 注册迁移事件回调
- `on_account_trade(callback)` - 注册账户交易事件回调
- `on_token_trade(callback)` - 注册代币交易事件回调

## 许可证

MIT