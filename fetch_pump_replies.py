#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pump代币回复数据采集脚本
定期从Pump API获取高价值代币的回复数据，并存入数据库
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# 确保可以导入src模块
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.api.pump_data_processor import PumpDataProcessor, ensure_token_replies_table

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pump_replies_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PumpRepliesFetcher")


def fetch_replies(sol_threshold: float = 35.0, 
                  cookie: str = "", 
                  use_proxy: bool = False, 
                  interval: int = 3600):
    """
    主循环，定期获取高价值代币的回复数据
    
    参数:
        sol_threshold: SOL数量阈值
        cookie: 可选的Cookie字符串
        use_proxy: 是否使用代理
        interval: 运行间隔（秒）
    """
    # 确保表存在
    if not ensure_token_replies_table():
        logger.error("无法创建必要的数据库表，程序退出")
        return 1
    
    run_count = 0
    try:
        while True:
            run_count += 1
            logger.info(f"开始第 {run_count} 次数据采集 (SOL阈值: {sol_threshold})")
            
            start_time = time.time()
            
            # 创建数据处理器
            with PumpDataProcessor(cookie=cookie, use_proxy=use_proxy) as processor:
                # 处理高价值代币的回复
                processor.process_high_value_tokens(sol_threshold=sol_threshold)
            
            # 计算运行时间
            elapsed_time = time.time() - start_time
            logger.info(f"第 {run_count} 次数据采集完成，耗时: {elapsed_time:.2f} 秒")
            
            # 等待下一次运行
            next_run = datetime.fromtimestamp(time.time() + interval)
            logger.info(f"下一次采集将在 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 开始")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        return 1
    
    return 0


def main():
    """解析命令行参数并运行数据采集"""
    parser = argparse.ArgumentParser(description="Pump代币回复数据采集工具")
    parser.add_argument("--sol", type=float, default=35.0, 
                       help="SOL数量阈值，只处理bonding curve中SOL大于此值的代币")
    parser.add_argument("--cookie", type=str, default="", 
                       help="Cookie字符串，用于身份验证")
    parser.add_argument("--proxy", action="store_true", 
                       help="是否使用代理")
    parser.add_argument("--interval", type=int, default=3600, 
                       help="运行间隔（秒），默认为1小时")
    parser.add_argument("--once", action="store_true", 
                       help="只运行一次，不循环")
    
    args = parser.parse_args()
    
    logger.info(f"启动Pump代币回复数据采集工具")
    logger.info(f"SOL阈值: {args.sol}, 使用代理: {args.proxy}, 运行间隔: {args.interval}秒")
    
    if args.once:
        # 只运行一次
        logger.info("单次运行模式")
        # 确保表存在
        if not ensure_token_replies_table():
            logger.error("无法创建必要的数据库表，程序退出")
            return 1
        
        # 创建数据处理器
        with PumpDataProcessor(cookie=args.cookie, use_proxy=args.proxy) as processor:
            # 处理高价值代币的回复
            processor.process_high_value_tokens(sol_threshold=args.sol)
    else:
        # 循环运行
        return fetch_replies(
            sol_threshold=args.sol, 
            cookie=args.cookie, 
            use_proxy=args.proxy, 
            interval=args.interval
        )
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 