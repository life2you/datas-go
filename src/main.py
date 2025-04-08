#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目主入口点
提供命令行接口以启动不同的服务
"""

import sys
import os
import argparse
import logging
import importlib
import subprocess
from pathlib import Path

# 确保src包可被导入
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import setup_logging
from src.core.error_handler import setup_error_handling
from src.core.config import LOG_DIR

# 配置日志和错误处理
setup_logging()
setup_error_handling()
logger = logging.getLogger("Main")

def ensure_log_directory():
    """确保日志目录存在"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        logger.info(f"创建日志目录: {LOG_DIR}")

def start_api(debug=False):
    """启动API服务器"""
    logger.info("正在启动API服务器...")
    try:
        # 动态导入避免循环依赖
        api_module = importlib.import_module("run_api")
        # 调用API服务器的主函数
        return api_module.main()
    except ImportError as e:
        logger.error(f"启动API服务器失败: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"API服务器运行异常: {str(e)}", exc_info=True)
        return 1

def start_fetch_replies(debug=False):
    """启动代币回复采集服务"""
    logger.info("正在启动代币回复采集服务...")
    try:
        # 动态导入避免循环依赖
        module = importlib.import_module("fetch_pump_replies")
        # 调用采集服务的主函数
        return module.main()
    except ImportError as e:
        logger.error(f"启动代币回复采集服务失败: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"代币回复采集服务运行异常: {str(e)}", exc_info=True)
        return 1

def start_service(service_name, debug=False):
    """启动指定的服务"""
    ensure_log_directory()
    
    if service_name == "api":
        return start_api(debug)
    elif service_name == "replies":
        return start_fetch_replies(debug)
    else:
        logger.error(f"未知服务名称: {service_name}")
        return 1

def stop_service(service_name):
    """停止指定的服务"""
    logger.info(f"正在停止服务: {service_name}")
    
    # 通过ps命令查找相关进程
    try:
        if service_name == "api":
            cmd = "ps aux | grep '[p]ython.*run_api.py' | awk '{print $2}'"
        elif service_name == "replies":
            cmd = "ps aux | grep '[p]ython.*fetch_pump_replies.py' | awk '{print $2}'"
        else:
            logger.error(f"未知服务名称: {service_name}")
            return 1
        
        # 执行命令获取进程ID
        output = subprocess.check_output(cmd, shell=True, text=True)
        pids = output.strip().split('\n')
        
        # 终止找到的进程
        for pid in pids:
            if pid:
                logger.info(f"正在终止进程 {pid}")
                subprocess.run(f"kill {pid}", shell=True)
        
        logger.info(f"服务 {service_name} 已停止")
        return 0
    except subprocess.CalledProcessError:
        logger.info(f"未找到服务 {service_name} 的运行进程")
        return 0
    except Exception as e:
        logger.error(f"停止服务 {service_name} 失败: {str(e)}", exc_info=True)
        return 1

def main():
    """主函数，解析命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(description="数据采集与API服务管理工具")
    parser.add_argument("action", choices=["start", "stop", "restart", "debug"], 
                        help="要执行的动作: start - 启动服务, stop - 停止服务, restart - 重启服务, debug - 在调试模式下启动")
    parser.add_argument("service", choices=["api", "replies", "all"], 
                        help="要操作的服务: api - API服务, replies - 代币回复采集服务, all - 所有服务")
    
    args = parser.parse_args()
    
    # 根据命令行参数执行相应操作
    if args.service == "all":
        services = ["api", "replies"]
    else:
        services = [args.service]
    
    if args.action == "start":
        # 启动服务
        for service in services:
            start_service(service)
    elif args.action == "stop":
        # 停止服务
        for service in services:
            stop_service(service)
    elif args.action == "restart":
        # 重启服务
        for service in services:
            stop_service(service)
            start_service(service)
    elif args.action == "debug":
        # 调试模式启动
        for service in services:
            start_service(service, debug=True)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 