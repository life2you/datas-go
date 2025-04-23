# TODO List

此列表记录了 Solana 区块解析器项目的待办事项。

## 核心功能

- [ ] **指令解析实现 (Parser):**
    - [ ] 实现 `internal/parser/parser.go` 中的 `parseTokenInstruction` 函数：
        - [ ] 使用 Borsh 反序列化 SPL Token 指令数据。
        - [ ] 正确处理 `InitializeMint` 指令，提取 `Decimals`, `MintAuthority`, `FreezeAuthority` (可选)。设置 `parsedTx.Type = models.TxTypeTokenCreation` 并填充 `TokenCreationDetails`。
        - [ ] 正确处理 `Transfer` 和 `TransferChecked` 指令，提取 `Source`, `Destination`, `Amount`, `Mint` (通过账户), `Decimals` (仅 TransferChecked 数据)。设置 `parsedTx.Type = models.TxTypeTokenTransfer` 并填充 `TokenTransferDetails`。
        - [ ] (可选) 处理其他 SPL Token 指令 (如 `MintTo`, `Burn`)。
    - [ ] 实现 `internal/parser/parser.go` 中的 `parseSystemInstruction` 函数 (如果需要区分 SOL 转账)。
        - [ ] 使用 Borsh 反序列化 System Program 指令数据。
        - [ ] 处理 `Transfer` 指令，提取 `Source`, `Destination`, `Lamports`。
    - [ ] 实现 `internal/parser/parser.go` 中至少一个 DEX Swap 指令的解析函数 (例如 `parseRaydiumSwap`)：
        - [ ] 确定 Raydium Swap 指令的 Program ID 和指令判别符/布局。
        - [ ] 使用 Borsh 或特定布局反序列化指令数据。
        - [ ] 提取 `UserAccount`, `AmountIn`, `MintIn`, `AmountOut`, `MintOut` 等关键信息。设置 `parsedTx.Type = models.TxTypeTokenSwap` 并填充 `TokenSwapDetails`。
    - [ ] 处理地址查找表 (ALT)：
        - [ ] 在 `ParseTransaction` 中检查 `tx.Message.Decompile()` 返回的 `MessageAddressTableLookup` 是否存在。
        - [ ] 如果存在，在 `internal/rpc/client.go` 中添加 `GetAccountInfo` 方法。
        - [ ] 调用 RPC 获取 ALT 账户数据。
        - [ ] 反序列化 ALT 账户数据 (Borsh 格式的地址列表)。
        - [ ] 合并静态账户列表和 ALT 提供的账户列表。
        - [ ] 确保后续的 `ResolveProgramIDIndex` 和账户索引解析使用合并后的列表。

- [ ] **状态管理:**
    - [x] 在 `cmd/block_parser/main.go` 中实现 `lastProcessedSlot` 的持久化存储（例如写入文件）。
    - [x] 程序启动时加载 `lastProcessedSlot`。

- [ ] **配置管理:**
    - [x] 将 RPC 端点、轮询间隔等参数移至配置文件 (e.g., `config.yaml`) 或环境变量。
    - [x] 添加读取配置的代码。

## WebSocket 功能

- [x] **基础 WebSocket 客户端:**
    - [x] 实现 WebSocket 连接到 Helius 服务。
    - [x] 实现自动重连机制。
    - [x] 实现 ping/pong 心跳检测。

- [x] **订阅功能:**
    - [x] 实现账户订阅 (AccountSubscribe)。
    - [x] 实现程序订阅 (ProgramSubscribe)。
    - [x] 实现插槽订阅 (SlotSubscribe)。
    - [x] 实现签名订阅 (SignatureSubscribe)。
    - [x] 实现日志订阅 (LogsSubscribe)。
    - [x] 实现区块订阅 (BlockSubscribe)。

- [ ] **WebSocket 使用整合:**
    - [x] 创建 WebSocket 使用示例。
    - [x] 将 WebSocket 方式集成到区块解析器中，作为替代轮询的方式。
    - [x] 实现基于 BlockSubscribe 的区块数据存储功能。

## Redis 存储功能

- [x] **基础 Redis 存储功能:**
    - [x] 实现 Redis 客户端连接与管理。
    - [x] 实现区块数据存储功能 (StoreBlock)。
    - [x] 实现区块数据检索功能 (GetBlockBySlot)。
    - [x] 实现最小/最大区块高度获取功能。
    - [x] 添加区块存在性检查、区块计数等辅助功能。

- [ ] **高级 Redis 功能:**
    - [ ] 实现区块数据过期策略，自动清理过旧的区块数据。
    - [ ] 添加交易索引，支持通过交易哈希查询所在区块。
    - [ ] 实现账户索引，支持查询与指定账户相关的区块和交易。
    - [ ] 添加解析后的交易数据存储功能。

- [ ] **性能优化:**
    - [ ] 使用Redis流水线(pipeline)批量处理多个区块。
    - [ ] 考虑使用Redis集群以提高吞吐量。
    - [ ] 优化Redis内存使用，考虑使用压缩存储。

## 改进与优化

- [x] **错误处理:**
    - [x] 修复交易解析过程中的类型错误
    - [x] 修复RPC调用错误，在GetBlock方法中添加maxSupportedTransactionVersion参数
    - [ ] 更精细地处理 RPC 错误 (限流、节点暂时不可用等)。
    - [ ] 更健壮地处理解析错误 (无效数据、未知指令等)。
    - [ ] 实现重试机制 (针对 RPC 调用失败或特定错误)。
- [ ] **并发处理:**
    - [ ] 考虑并发处理区块或交易解析 (如果性能需要)。
- [x] **订阅模式:**
    - [x] 研究并实现使用 Solana WebSocket RPC 的 `slotSubscribe` 或其他订阅方式，替换轮询，以获得更低的延迟。
- [ ] **数据输出:**
    - [x] 将解析后的区块数据存储到Redis中。
    - [ ] 将解析后的 `ParsedTransaction` 数据发送到数据库 (如 PostgreSQL, ClickHouse)。
    - [ ] 将解析后的 `ParsedTransaction` 数据发送到消息队列 (如 Kafka, RabbitMQ)。
- [ ] **日志:**
    - [ ] 使用结构化日志库 (如 `logrus`, `zap`) 替代标准 `log`。
    - [ ] 调整日志级别和输出格式。

## 测试

- [x] **集成测试:**
    - [x] 创建测试工具验证交易解析功能
- [ ] 为 `internal/parser` 添加单元测试，覆盖各种指令的解析逻辑。
- [ ] 为 `internal/rpc` 添加模拟测试或集成测试。
- [ ] 为 WebSocket 客户端添加单元测试。
- [ ] 为 Redis 存储服务添加单元测试和集成测试。
- [ ] 为 `main.go` 的主流程添加集成测试。 