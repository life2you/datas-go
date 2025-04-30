# 更新日志

所有项目的显著变更都将记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 添加
- 实现了基于Helius的WebSocket客户端，支持连接到Solana区块链的实时数据流
- 添加了账户、程序、插槽、签名和日志订阅功能
- 实现了自动重连和心跳检测机制
- 添加了WebSocket客户端使用示例
- 实现了基于Redis的区块存储服务，支持区块数据的存储和高效检索
- 添加了获取最小/最大区块、区块范围、区块统计等功能
- 提供了Redis存储服务的使用示例
- **添加Helius区块订阅功能，支持通过WebSocket订阅并处理最新区块**
- **实现代理支持，可通过配置使用HTTP代理连接Helius WebSocket**
- **添加从Helius接收的区块数据存储到Redis的功能**
- **实现Helius Enhanced Transactions API支持，包括交易解析和丰富的交易历史查询功能**
  - **提供ParseTransactions函数，支持解析单个或多个交易签名为结构化数据**
  - **添加GetEnrichedTransactionHistory函数，支持按地址查询丰富的交易历史**
  - **支持各种查询参数，如分页、交易类型筛选等**
- **添加详细的Helius API使用文档，包括示例代码和配置说明**
- **支持通过代理连接Helius API服务，提高在特定网络环境下的稳定性**
- **实现了完整的错误处理和响应解析机制，提高了API调用的可靠性**
- **新增Helius Webhook支持，允许监控Solana链上事件并通过回调接收通知**
  - **支持创建、获取、编辑和删除Webhook**
  - **支持处理接收到的Webhook事件**
  - **支持多种交易类型过滤，如NFT销售、代币转账等**
  - **添加了示例处理函数和使用说明**
- **实现PumpPortal WebSocket客户端，支持连接PumpPortal实时数据API**
  - **添加新代币创建事件订阅(subscribeNewToken)功能**
  - **添加代币交易事件订阅(subscribeTokenTrade)功能**
  - **添加账户交易事件订阅(subscribeAccountTrade)功能**
  - **添加代币迁移事件订阅(subscribeMigration)功能**
  - **实现自动重连和心跳检测机制**
  - **支持通过代理连接PumpPortal WebSocket**
  - **添加完整使用示例**

### 修复
- 修复了RPC调用错误，在GetBlock方法中添加了maxSupportedTransactionVersion参数

## [0.1.0] - 2024-XX-XX

### 添加
- 初始版本的Solana区块解析器
- RPC客户端实现，支持获取最新区块高度和区块数据
- 基本的交易解析功能 