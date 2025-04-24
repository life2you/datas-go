package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/life2you/datas-go/handler"
	"io/ioutil"
	"log"
	"os"

	"github.com/life2you/datas-go/models/resp"
)

func main() {
	// 定义命令行参数
	txType := flag.String("tx-type", "", "交易类型 (SWAP, TRANSFER, etc.)")
	sampleFile := flag.String("sample-file", "", "包含交易数据的样例文件路径")

	flag.Parse()

	// 验证必要参数
	if *txType == "" {
		log.Fatal("必须指定交易类型，使用 --tx-type 参数")
	}

	if *sampleFile == "" {
		log.Fatal("必须指定样例文件，使用 --sample-file 参数")
	}

	// 读取样例文件
	data, err := ioutil.ReadFile(*sampleFile)
	if err != nil {
		log.Fatalf("无法读取样例文件: %v", err)
	}

	// 解析交易数据
	var transaction resp.ParsedTransaction
	if err := json.Unmarshal(data, &transaction); err != nil {
		log.Fatalf("解析JSON失败: %v", err)
	}

	// 根据交易类型调用相应的解析函数
	var result string
	switch resp.TransactionType(*txType) {
	case resp.TransactionTypeSwap:
		result = handler.ParseSwapTransaction(&transaction)
	// 可以根据需要添加其他交易类型的解析
	// case resp.TransactionTypeTransfer:
	//     result = resp.ParseTransferTransaction(&transaction)
	default:
		fmt.Printf("不支持的交易类型: %s\n", *txType)
		os.Exit(1)
	}

	// 输出结果
	fmt.Println("解析结果:")
	fmt.Println(result)
}
