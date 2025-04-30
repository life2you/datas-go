package resp

import "github.com/shopspring/decimal"

type MessageType string

const (
	Create  MessageType = "create"
	Migrate MessageType = "migrate"
)

type ClassifyType struct {
	TxType MessageType `json:"txType"`
}

type NewToken struct {
	Signature             string          `json:"signature"`
	Mint                  string          `json:"mint"`
	TraderPublicKey       string          `json:"traderPublicKey"`
	TxType                MessageType     `json:"txType"`
	InitialBuy            decimal.Decimal `json:"initialBuy"`
	SolAmount             decimal.Decimal `json:"solAmount"`
	BondingCurveKey       string          `json:"bondingCurveKey"`
	VTokensInBondingCurve decimal.Decimal `json:"vTokensInBondingCurve"`
	VSolInBondingCurve    decimal.Decimal `json:"vSolInBondingCurve"`
	MarketCapSol          decimal.Decimal `json:"marketCapSol"`
	Name                  string          `json:"name"`
	Symbol                string          `json:"symbol"`
	URI                   string          `json:"uri"`
	Pool                  string          `json:"pool"`
}

type MigrateMode struct {
	Signature string      `json:"signature"`
	Mint      string      `json:"mint"`
	TxType    MessageType `json:"txType"`
	Pool      string      `json:"pool"`
}
