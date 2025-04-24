package resp

type BlockResp struct {
	BlockTime         int            `json:"blockTime"`
	Blockhash         string         `json:"blockhash"`
	ParentSlot        int            `json:"parentSlot"`
	PreviousBlockhash string         `json:"previousBlockhash"`
	Transactions      []Transactions `json:"transactions"`
}
type Rewards struct {
	Commission  interface{} `json:"commission"`
	Lamports    int         `json:"lamports"`
	PostBalance int64       `json:"postBalance"`
	Pubkey      string      `json:"pubkey"`
	RewardType  string      `json:"rewardType"`
}
type Err struct {
	InstructionError []interface{} `json:"InstructionError"`
}
type LoadedAddresses struct {
	Readonly []string      `json:"readonly"`
	Writable []interface{} `json:"writable"`
}
type UITokenAmount struct {
	Amount         string  `json:"amount"`
	Decimals       int     `json:"decimals"`
	UIAmount       float64 `json:"uiAmount"`
	UIAmountString string  `json:"uiAmountString"`
}
type PostTokenBalances struct {
	AccountIndex  int           `json:"accountIndex"`
	Mint          string        `json:"mint"`
	Owner         string        `json:"owner"`
	ProgramID     string        `json:"programId"`
	UITokenAmount UITokenAmount `json:"uiTokenAmount"`
}
type PreTokenBalances struct {
	AccountIndex  int           `json:"accountIndex"`
	Mint          string        `json:"mint"`
	Owner         string        `json:"owner"`
	ProgramID     string        `json:"programId"`
	UITokenAmount UITokenAmount `json:"uiTokenAmount"`
}
type Meta struct {
	ComputeUnitsConsumed int                 `json:"computeUnitsConsumed"`
	Err                  Err                 `json:"err"`
	Fee                  int                 `json:"fee"`
	InnerInstructions    []interface{}       `json:"innerInstructions"`
	LoadedAddresses      LoadedAddresses     `json:"loadedAddresses"`
	LogMessages          []string            `json:"logMessages"`
	PostBalances         []interface{}       `json:"postBalances"`
	PostTokenBalances    []PostTokenBalances `json:"postTokenBalances"`
	PreBalances          []interface{}       `json:"preBalances"`
	PreTokenBalances     []PreTokenBalances  `json:"preTokenBalances"`
	Rewards              []interface{}       `json:"rewards"`
	Status               Status              `json:"status"`
}
type AddressTableLookups struct {
	AccountKey      string        `json:"accountKey"`
	ReadonlyIndexes []int         `json:"readonlyIndexes"`
	WritableIndexes []interface{} `json:"writableIndexes"`
}
type Header struct {
	NumReadonlySignedAccounts   int `json:"numReadonlySignedAccounts"`
	NumReadonlyUnsignedAccounts int `json:"numReadonlyUnsignedAccounts"`
	NumRequiredSignatures       int `json:"numRequiredSignatures"`
}
type Instructions struct {
	Accounts       []interface{} `json:"accounts"`
	Data           string        `json:"data"`
	ProgramIDIndex int           `json:"programIdIndex"`
	StackHeight    interface{}   `json:"stackHeight"`
}
type Message struct {
	AccountKeys         []string              `json:"accountKeys"`
	AddressTableLookups []AddressTableLookups `json:"addressTableLookups"`
	Header              Header                `json:"header"`
	Instructions        []Instructions        `json:"instructions"`
	RecentBlockhash     string                `json:"recentBlockhash"`
}
type Transaction struct {
	Message    Message  `json:"message"`
	Signatures []string `json:"signatures"`
}
type InnerInstructions struct {
	Index        int            `json:"index"`
	Instructions []Instructions `json:"instructions"`
}
type ReturnData struct {
	Data      []string `json:"data"`
	ProgramID string   `json:"programId"`
}
type Status struct {
	Ok  interface{} `json:"Ok"`
	Err Err         `json:"Err"`
}
type Meta0 struct {
	ComputeUnitsConsumed int                 `json:"computeUnitsConsumed"`
	Err                  interface{}         `json:"err"`
	Fee                  int                 `json:"fee"`
	InnerInstructions    []InnerInstructions `json:"innerInstructions"`
	LoadedAddresses      LoadedAddresses     `json:"loadedAddresses"`
	LogMessages          []string            `json:"logMessages"`
	PostBalances         []interface{}       `json:"postBalances"`
	PostTokenBalances    []PostTokenBalances `json:"postTokenBalances"`
	PreBalances          []interface{}       `json:"preBalances"`
	PreTokenBalances     []PreTokenBalances  `json:"preTokenBalances"`
	ReturnData           ReturnData          `json:"returnData"`
	Rewards              []interface{}       `json:"rewards"`
	Status               Status              `json:"status"`
}
type Meta1 struct {
	ComputeUnitsConsumed int                 `json:"computeUnitsConsumed"`
	Err                  interface{}         `json:"err"`
	Fee                  int                 `json:"fee"`
	InnerInstructions    []InnerInstructions `json:"innerInstructions"`
	LoadedAddresses      LoadedAddresses     `json:"loadedAddresses"`
	LogMessages          []string            `json:"logMessages"`
	PostBalances         []interface{}       `json:"postBalances"`
	PostTokenBalances    []PostTokenBalances `json:"postTokenBalances"`
	PreBalances          []interface{}       `json:"preBalances"`
	PreTokenBalances     []PreTokenBalances  `json:"preTokenBalances"`
	ReturnData           ReturnData          `json:"returnData"`
	Rewards              []interface{}       `json:"rewards"`
	Status               Status              `json:"status"`
}
type Meta2 struct {
	ComputeUnitsConsumed int                 `json:"computeUnitsConsumed"`
	Err                  interface{}         `json:"err"`
	Fee                  int                 `json:"fee"`
	InnerInstructions    []InnerInstructions `json:"innerInstructions"`
	LoadedAddresses      LoadedAddresses     `json:"loadedAddresses"`
	LogMessages          []string            `json:"logMessages"`
	PostBalances         []interface{}       `json:"postBalances"`
	PostTokenBalances    []PostTokenBalances `json:"postTokenBalances"`
	PreBalances          []interface{}       `json:"preBalances"`
	PreTokenBalances     []PreTokenBalances  `json:"preTokenBalances"`
	ReturnData           ReturnData          `json:"returnData"`
	Rewards              []interface{}       `json:"rewards"`
	Status               Status              `json:"status"`
}
type Transactions struct {
	Meta        Meta        `json:"meta"`
	Transaction Transaction `json:"transaction"`
	Version     any         `json:"version"`
}
