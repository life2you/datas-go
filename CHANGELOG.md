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

### 修复
- 修复了RPC调用错误，在GetBlock方法中添加了maxSupportedTransactionVersion参数

## [0.1.0] - 2024-XX-XX

### 添加
- 初始版本的Solana区块解析器
- RPC客户端实现，支持获取最新区块高度和区块数据
- 基本的交易解析功能 