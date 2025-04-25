package models

type TransactionQueueModel struct {
	Signatures []string `json:"signatures"`
	Slot       uint64   `json:"slot"`
}
