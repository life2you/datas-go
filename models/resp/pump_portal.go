package resp

import "github.com/shopspring/decimal"

type NewToken struct {
	Signature             string          `json:"signature"`
	Mint                  string          `json:"mint"`
	TraderPublicKey       string          `json:"traderPublicKey"`
	TxType                string          `json:"txType"`
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
