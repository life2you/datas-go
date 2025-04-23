package models

// TxType 交易类型枚举
type TxType string

const (
	TxTypeUnknown TxType = "Unknown"

	// System Program
	TxTypeSystemCreateAccount TxType = "SystemCreateAccount" // 创建账户
	TxTypeSystemTransfer      TxType = "SystemTransfer"      // SOL 转账
	TxTypeSystemAssign        TxType = "SystemAssign"
	TxTypeSystemAllocate      TxType = "SystemAllocate"
	// ... 其他 System Program 类型

	// SPL Token Program
	TxTypeTokenCreation      TxType = "TokenCreation"     // InitializeMint (代币创建)
	TxTypeTokenMintTo        TxType = "TokenMintTo"       // 铸造代币
	TxTypeTokenTransfer      TxType = "TokenTransfer"     // Transfer/TransferChecked (代币转账)
	TxTypeTokenBurn          TxType = "TokenBurn"         // 销毁代币
	TxTypeTokenApprove       TxType = "TokenApprove"      // 授权委托
	TxTypeTokenRevoke        TxType = "TokenRevoke"       // 撤销委托
	TxTypeTokenSetAuthority  TxType = "TokenSetAuthority" // 设置权限
	TxTypeTokenCloseAccount  TxType = "TokenCloseAccount" // 关闭代币账户
	TxTypeTokenFreezeAccount TxType = "TokenFreezeAccount"
	TxTypeTokenThawAccount   TxType = "TokenThawAccount"

	// Associated Token Account Program
	TxTypeATACreation TxType = "ATACreation" // 创建关联代币账户

	// SPL Memo Program
	TxTypeMemo TxType = "Memo"

	// Stake Program
	TxTypeStakeCreateAccount TxType = "StakeCreateAccount"
	TxTypeStakeDelegate      TxType = "StakeDelegate"
	TxTypeStakeWithdraw      TxType = "StakeWithdraw"
	TxTypeStakeDeactivate    TxType = "StakeDeactivate"
	// ... 其他 Stake Program 类型

	// Compute Budget Program
	TxTypeComputeBudgetRequestUnits TxType = "ComputeBudgetRequestUnits"
	TxTypeComputeBudgetSetPrice     TxType = "ComputeBudgetSetPrice"

	// Address Lookup Table Program
	TxTypeALTCreateLookupTable     TxType = "ALTCreateLookupTable"
	TxTypeALTExtendLookupTable     TxType = "ALTExtendLookupTable"
	TxTypeALTFreezeLookupTable     TxType = "ALTFreezeLookupTable"
	TxTypeALTDeactivateLookupTable TxType = "ALTDeactivateLookupTable"
	TxTypeALTCloseLookupTable      TxType = "ALTCloseLookupTable"

	// Decentralized Exchanges (DEX) - 通用或特定
	TxTypeTokenSwap       TxType = "TokenSwap"       // 通用代币交换 (买卖)
	TxTypeLiquidityAdd    TxType = "LiquidityAdd"    // 添加流动性
	TxTypeLiquidityRemove TxType = "LiquidityRemove" // 移除流动性
	// ... 特定 DEX (Raydium, Orca) 的更具体类型可能需要单独定义

	// Non-Fungible Tokens (NFT) - Metaplex & Marketplaces
	TxTypeNFTMint           TxType = "NFTMint"       // Metaplex 创建/铸造 NFT
	TxTypeNFTTransfer       TxType = "NFTTransfer"   // NFT 转账 (本质是 SPL Token Transfer)
	TxTypeNFTList           TxType = "NFTList"       // 市场挂单
	TxTypeNFTCancelList     TxType = "NFTCancelList" // 取消挂单
	TxTypeNFTBuy            TxType = "NFTBuy"        // 市场购买
	TxTypeNFTUpdateMetadata TxType = "NFTUpdateMetadata"
	// ... Candy Machine, Auction House 等操作

	// Lending Protocols
	TxTypeLendingDeposit   TxType = "LendingDeposit"
	TxTypeLendingWithdraw  TxType = "LendingWithdraw"
	TxTypeLendingBorrow    TxType = "LendingBorrow"
	TxTypeLendingRepay     TxType = "LendingRepay"
	TxTypeLendingLiquidate TxType = "LendingLiquidate"

	// Solana Name Service (SNS)
	TxTypeSNSDomainRegister TxType = "SNSDomainRegister"
	TxTypeSNSDomainTransfer TxType = "SNSDomainTransfer"

	// 请注意：许多复杂的 DeFi 操作可能涉及多个指令，
	// 可能需要更复杂的逻辑来将其归类为一个高级操作类型，
	// 或者保留为多个基础指令类型。
)
