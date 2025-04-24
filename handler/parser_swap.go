package handler

import (
	"fmt"
	"github.com/life2you/datas-go/models/resp"
	"github.com/shopspring/decimal"
)

// ParseSwapTransaction 解析 Swap 交易，返回人类可读格式
// 例如：地址A 1SOL 购买 100代币1 或 地址A 100代币1 卖出 1SOL
func ParseSwapTransaction(tx *resp.ParsedTransaction) string {
	if tx == nil || tx.Events == nil || tx.Events.Swap == nil {
		return "无效的Swap交易"
	}

	swap := tx.Events.Swap

	// 确定交易方向和账户
	var account string
	var isBuy bool
	var solAmount string
	var tokenAmount string
	var tokenMint string
	var tokenDecimals int

	// 检查是否有SOL输入（卖出SOL）
	if swap.NativeInput != nil {
		account = swap.NativeInput.Account
		solAmount = swap.NativeInput.Amount
		isBuy = true // 用SOL购买代币

		// 找出代币输出
		if len(swap.TokenOutputs) > 0 {
			tokenMint = swap.TokenOutputs[0].Mint
			tokenAmount = swap.TokenOutputs[0].RawTokenAmount.TokenAmount
			tokenDecimals = swap.TokenOutputs[0].RawTokenAmount.Decimals
		}
	} else if swap.NativeOutput != nil {
		// 检查是否有SOL输出（买入SOL）
		account = swap.NativeOutput.Account
		solAmount = swap.NativeOutput.Amount
		isBuy = false // 卖出代币获得SOL

		// 找出代币输入
		if len(swap.TokenInputs) > 0 {
			tokenMint = swap.TokenInputs[0].Mint
			tokenAmount = swap.TokenInputs[0].RawTokenAmount.TokenAmount
			tokenDecimals = swap.TokenInputs[0].RawTokenAmount.Decimals
		}
	} else if len(swap.TokenInputs) > 0 && len(swap.TokenOutputs) > 0 {
		// 如果只有代币之间的交换
		account = swap.TokenInputs[0].UserAccount
		tokenMint = swap.TokenInputs[0].Mint
		tokenAmount = swap.TokenInputs[0].RawTokenAmount.TokenAmount
		tokenDecimals = swap.TokenInputs[0].RawTokenAmount.Decimals

		// 这里是代币间交换，可以扩展解析
		return fmt.Sprintf("地址%s 用 %s个%s 交换了 %s个%s",
			formatShortAddress(account),
			formatTokenAmount(tokenAmount, tokenDecimals),
			getTokenSymbol(tokenMint),
			formatTokenAmount(swap.TokenOutputs[0].RawTokenAmount.TokenAmount, swap.TokenOutputs[0].RawTokenAmount.Decimals),
			getTokenSymbol(swap.TokenOutputs[0].Mint))
	}

	// 转换数值并格式化输出
	solValue := formatSolAmount(solAmount)
	tokenValue := formatTokenAmount(tokenAmount, tokenDecimals)

	if isBuy {
		return fmt.Sprintf("地址%s 用 %s SOL 购买了 %s个%s",
			formatShortAddress(account), solValue, tokenValue, getTokenSymbol(tokenMint))
	} else {
		return fmt.Sprintf("地址%s 卖出 %s个%s 获得了 %s SOL",
			formatShortAddress(account), tokenValue, getTokenSymbol(tokenMint), solValue)
	}
}

// formatSolAmount 格式化SOL金额（转换为小数）
func formatSolAmount(amount string) string {
	value, _ := decimal.NewFromString(amount)
	return value.Div(decimal.New(1, 9)).String() // SOL有9位小数
}

// formatTokenAmount 格式化代币金额
func formatTokenAmount(amount string, decimals int) string {
	value, _ := decimal.NewFromString(amount)
	return value.Div(decimal.New(1, int32(decimals))).String()
}

// getTokenSymbol 获取代币符号（需要实现或集成代币元数据服务）
func getTokenSymbol(mint string) string {
	// 这里应该查询代币元数据获取符号
	// 简化实现，返回短地址
	if len(mint) > 8 {
		return mint[:8] + "..."
	}
	return mint
}

// formatShortAddress 格式化地址显示
func formatShortAddress(address string) string {
	if len(address) > 8 {
		return address[:4] + "..." + address[len(address)-4:]
	}
	return address
}
