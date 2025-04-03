#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 定义日志文件路径
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/pump_portal.log"
ERROR_LOG_FILE="${LOG_DIR}/pump_portal_error.log"

# 确保日志目录存在
mkdir -p ${LOG_DIR}

# 检查是否已有服务运行
check_service() {
    PID=$(ps aux | grep "python run_api.py" | grep -v grep | awk '{print $2}')
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}服务已在运行，PID: ${PID}${NC}"
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    echo -e "${GREEN}正在启动 API 服务...${NC}"
    echo -e "${YELLOW}启动命令: python run_api.py${NC}"
    
    # 直接前台运行以显示输出
    if [[ "$1" == "debug" ]]; then
        echo -e "${YELLOW}调试模式启动，输出将显示在控制台...${NC}"
        python run_api.py
        return
    fi
    
    # 后台运行
    nohup python run_api.py > ${LOG_DIR}/startup.log 2>&1 &
    PID=$!
    
    # 等待服务启动
    sleep 3
    
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}服务启动成功，PID: ${PID}${NC}"
        echo -e "${GREEN}API地址: http://127.0.0.1:8000${NC}"
        echo -e "${GREEN}API文档: http://127.0.0.1:8000/docs${NC}"
    else
        echo -e "${RED}服务启动失败，请检查错误日志${NC}"
        echo -e "${YELLOW}查看启动日志: cat ${LOG_DIR}/startup.log${NC}"
        cat ${LOG_DIR}/startup.log
        exit 1
    fi
}

# 显示实时日志
show_logs() {
    echo -e "${GREEN}显示实时日志...${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止查看日志${NC}"
    tail -f ${LOG_FILE}
}

# 显示错误日志
show_error_logs() {
    echo -e "${GREEN}显示错误日志...${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止查看日志${NC}"
    tail -f ${ERROR_LOG_FILE}
}

# 停止服务
stop_service() {
    PID=$(ps aux | grep "python run_api.py" | grep -v grep | awk '{print $2}')
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}正在停止服务，PID: ${PID}${NC}"
        kill -9 $PID
        echo -e "${GREEN}服务已停止${NC}"
    else
        echo -e "${YELLOW}没有运行中的服务${NC}"
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 1
    start_service
}

# 主脚本逻辑
case "$1" in
    start)
        if ! check_service; then
            start_service
        fi
        ;;
    debug)
        if ! check_service; then
            start_service debug
        fi
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        show_logs
        ;;
    errors)
        show_error_logs
        ;;
    status)
        if check_service; then
            echo -e "${GREEN}服务正在运行${NC}"
        else
            echo -e "${RED}服务未运行${NC}"
        fi
        ;;
    *)
        echo "用法: $0 {start|debug|stop|restart|logs|errors|status}"
        echo "  start   - 启动服务"
        echo "  debug   - 以调试模式启动服务（前台运行）"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  logs    - 查看实时日志"
        echo "  errors  - 查看错误日志"
        echo "  status  - 检查服务状态"
        exit 1
        ;;
esac

exit 0 