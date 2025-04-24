package resp

import "github.com/shopspring/decimal"

var NeedToParseTransactionType = []TransactionType{
	TransactionTypeTransfer,
	TransactionTypeBurn,
	TransactionTypeTokenMint,
	TransactionTypeSwap,
	TransactionTypeInitializeAccount,
	//TransactionTypeUnknown,
	TransactionTypeUnlabeled,
}

// TransactionType 定义了 Helius 解析的交易类型
type TransactionType string

// 定义交易类型常量

// 通用与未知类型
const (
	TransactionTypeUnknown           TransactionType = "UNKNOWN"            // 未知或无法解析的交易
	TransactionTypeUnlabeled         TransactionType = "UNLABELED"          // 未标记的交易
	TransactionTypeTransfer          TransactionType = "TRANSFER"           // SOL 或 SPL 代币转账
	TransactionTypeBurn              TransactionType = "BURN"               // 销毁代币
	TransactionTypeInitializeAccount TransactionType = "INITIALIZE_ACCOUNT" // 初始化代币账户
	TransactionTypeTokenMint         TransactionType = "TOKEN_MINT"
	TransactionTypeSwap              TransactionType = "SWAP" // 代币交换
)

// ParsedTransaction 表示解析后的交易数据
type ParsedTransaction struct {
	Description      string            `json:"description"`
	Type             TransactionType   `json:"type"` // 使用枚举类型
	Source           string            `json:"source"`
	Fee              int64             `json:"fee"`
	FeePayer         string            `json:"feePayer"`
	Signature        string            `json:"signature"`
	Slot             uint64            `json:"slot"`
	Timestamp        int64             `json:"timestamp"`
	NativeTransfers  []NativeTransfer  `json:"nativeTransfers"`
	TokenTransfers   []TokenTransfer   `json:"tokenTransfers"`
	AccountData      []AccountData     `json:"accountData"`
	TransactionError *TransactionError `json:"transactionError,omitempty"`
	Instructions     []Instruction     `json:"instructions"`
	Events           *Events           `json:"events,omitempty"`
}

// NativeTransfer 表示原生代币(SOL)转账
type NativeTransfer struct {
	FromUserAccount string `json:"fromUserAccount"`
	ToUserAccount   string `json:"toUserAccount"`
	Amount          int64  `json:"amount"`
}

// TokenTransfer 表示代币转账
type TokenTransfer struct {
	FromUserAccount  string          `json:"fromUserAccount"`
	ToUserAccount    string          `json:"toUserAccount"`
	FromTokenAccount string          `json:"fromTokenAccount"`
	ToTokenAccount   string          `json:"toTokenAccount"`
	TokenAmount      decimal.Decimal `json:"tokenAmount"`
	Mint             string          `json:"mint"`
}

// AccountData 表示账户数据变更
type AccountData struct {
	Account             string               `json:"account"`
	NativeBalanceChange int64                `json:"nativeBalanceChange"`
	TokenBalanceChanges []TokenBalanceChange `json:"tokenBalanceChanges,omitempty"`
}

// TokenBalanceChange 表示代币余额变更
type TokenBalanceChange struct {
	UserAccount    string         `json:"userAccount"`
	TokenAccount   string         `json:"tokenAccount"`
	Mint           string         `json:"mint"`
	RawTokenAmount RawTokenAmount `json:"rawTokenAmount"`
}

// RawTokenAmount 表示代币数量
type RawTokenAmount struct {
	TokenAmount string `json:"tokenAmount"`
	Decimals    int    `json:"decimals"`
}

// TransactionError 表示交易错误
type TransactionError struct {
	Error            string `json:"error"`
	InstructionError []any  `json:"instructionError"`
}

// Instruction 表示交易指令
type Instruction struct {
	Accounts          []string           `json:"accounts"`
	Data              string             `json:"data"`
	ProgramId         string             `json:"programId"`
	InnerInstructions []InnerInstruction `json:"innerInstructions,omitempty"`
}

// InnerInstruction 表示内部指令
type InnerInstruction struct {
	Accounts  []string `json:"accounts"`
	Data      string   `json:"data"`
	ProgramId string   `json:"programId"`
}

// Events 表示交易事件
type Events struct {
	//NFT                          *NFTEvent                     `json:"nft,omitempty"`
	Swap *SwapEvent `json:"swap,omitempty"`
	//Compressed                   *CompressedEvent              `json:"compressed,omitempty"`
	//DistributeCompressionRewards *DistributeCompressionRewards `json:"distributeCompressionRewards,omitempty"`
	//SetAuthority                 *SetAuthorityEvent            `json:"setAuthority,omitempty"`
}

// NFTEvent 表示NFT相关事件
type NFTEvent struct {
	Description string    `json:"description"`
	Type        string    `json:"type"`
	Source      string    `json:"source"`
	Amount      int64     `json:"amount"`
	Fee         int64     `json:"fee"`
	FeePayer    string    `json:"feePayer"`
	Signature   string    `json:"signature"`
	Slot        uint64    `json:"slot"`
	Timestamp   int64     `json:"timestamp"`
	SaleType    string    `json:"saleType"`
	Buyer       string    `json:"buyer"`
	Seller      string    `json:"seller"`
	Staker      string    `json:"staker,omitempty"`
	NFTs        []NFTInfo `json:"nfts"`
}

// NFTInfo 表示NFT信息
type NFTInfo struct {
	Mint          string `json:"mint"`
	TokenStandard string `json:"tokenStandard"`
}

// SwapEvent 表示代币交换事件
type SwapEvent struct {
	NativeInput  *NativeAmount        `json:"nativeInput,omitempty"`
	NativeOutput *NativeAmount        `json:"nativeOutput,omitempty"`
	TokenInputs  []TokenBalanceChange `json:"tokenInputs"`
	TokenOutputs []TokenBalanceChange `json:"tokenOutputs"`
	TokenFees    []TokenBalanceChange `json:"tokenFees,omitempty"`
	NativeFees   []NativeAmount       `json:"nativeFees,omitempty"`
	InnerSwaps   []InnerSwap          `json:"innerSwaps,omitempty"`
}

// NativeAmount 表示原生代币(SOL)数量
type NativeAmount struct {
	Account string `json:"account"`
	Amount  string `json:"amount"`
}

// InnerSwap 表示内部交换
type InnerSwap struct {
	TokenInputs  []TokenTransfer  `json:"tokenInputs"`
	TokenOutputs []TokenTransfer  `json:"tokenOutputs"`
	TokenFees    []TokenTransfer  `json:"tokenFees,omitempty"`
	NativeFees   []NativeTransfer `json:"nativeFees,omitempty"`
	ProgramInfo  ProgramInfo      `json:"programInfo"`
}

// ProgramInfo 表示程序信息
type ProgramInfo struct {
	Source          string `json:"source"`
	Account         string `json:"account"`
	ProgramName     string `json:"programName"`
	InstructionName string `json:"instructionName"`
}

// CompressedEvent 表示压缩NFT事件
type CompressedEvent struct {
	Type                  string `json:"type"`
	TreeId                string `json:"treeId"`
	AssetId               string `json:"assetId"`
	LeafIndex             int64  `json:"leafIndex"`
	InstructionIndex      int    `json:"instructionIndex"`
	InnerInstructionIndex int    `json:"innerInstructionIndex"`
	NewLeafOwner          string `json:"newLeafOwner"`
	OldLeafOwner          string `json:"oldLeafOwner"`
}

// DistributeCompressionRewards 表示压缩奖励分配
type DistributeCompressionRewards struct {
	Amount int64 `json:"amount"`
}

// SetAuthorityEvent 表示设置权限事件
type SetAuthorityEvent struct {
	Account               string `json:"account"`
	From                  string `json:"from"`
	To                    string `json:"to"`
	InstructionIndex      int    `json:"instructionIndex"`
	InnerInstructionIndex int    `json:"innerInstructionIndex"`
}

// EnrichedHistoryOptions 表示获取丰富交易历史的查询参数
type EnrichedHistoryOptions struct {
	Before    string   `json:"before,omitempty"`
	After     string   `json:"after,omitempty"`
	Limit     int      `json:"limit,omitempty"`
	Source    string   `json:"source,omitempty"`
	Types     []string `json:"types,omitempty"`
	BetaRPC   bool     `json:"beta_rpc,omitempty"`
	SortOrder string   `json:"sort_order,omitempty"`
}
