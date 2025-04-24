package req

// GetBlockParams 表示 getBlock 请求的参数选项
type GetBlockParams struct {
	Encoding                       string `json:"encoding"`
	TransactionDetails             string `json:"transactionDetails"`
	Rewards                        *bool  `json:"rewards"`
	MaxSupportedTransactionVersion int    `json:"maxSupportedTransactionVersion"`
	Commitment                     string `json:"commitment"`
}
