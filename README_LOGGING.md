# 日志系统使用说明

本项目采用了完善的日志系统，支持同时输出到控制台和文件，并将错误日志单独记录。

## 日志系统特点

- 控制台输出：所有日志同时在控制台显示
- 文件日志：所有日志记录到文件，支持自动轮转
- 错误日志：ERROR及以上级别的日志单独记录到错误日志文件
- 日志管理：提供工具脚本便于查看和管理日志文件

## 配置项

在 `.env` 文件中可以配置以下日志相关参数：

```
# 日志配置
LOG_LEVEL=INFO
# 日志文件配置
LOG_DIR=logs
LOG_FILE=pump_portal.log
LOG_ERROR_FILE=pump_portal_error.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
LOG_TO_FILE=true
```

参数说明：
- `LOG_LEVEL`：日志记录级别，可选值为 DEBUG、INFO、WARNING、ERROR、CRITICAL
- `LOG_DIR`：日志文件存放目录
- `LOG_FILE`：主日志文件名称
- `LOG_ERROR_FILE`：错误日志文件名称
- `LOG_MAX_BYTES`：单个日志文件的最大大小（字节），默认10MB
- `LOG_BACKUP_COUNT`：最多保留的日志文件备份数量
- `LOG_TO_FILE`：是否将日志写入文件，设为 false 则只输出到控制台

## 在代码中使用日志

在代码中使用日志系统非常简单：

```python
from src.utils.logger import get_logger

# 创建一个日志记录器，通常使用当前模块名称
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息，详细的内部状态记录")
logger.info("普通信息，确认程序按预期运行")
logger.warning("警告信息，表示可能出现的问题")
logger.error("错误信息，程序某些功能无法正常运行")
logger.critical("严重错误，程序可能无法继续运行")
```

## 使用日志管理工具

项目提供了一个日志管理工具 `log_tools.py`，可以方便地查看和管理日志文件：

### 列出所有日志文件

```bash
python log_tools.py list
```

### 查看日志内容

查看普通日志文件的最后100行：
```bash
python log_tools.py view
```

查看错误日志：
```bash
python log_tools.py view -e
```

查看指定日志文件：
```bash
python log_tools.py view -f pump_portal.log.1
```

查看指定行数：
```bash
python log_tools.py view -n 50
```

根据关键词过滤日志：
```bash
python log_tools.py view -p "error|exception"
```

### 清除日志文件

```bash
python log_tools.py clear
```

添加 `-y` 参数可以跳过确认：
```bash
python log_tools.py clear -y
```

### 备份日志文件

备份日志到自动生成的时间戳目录：
```bash
python log_tools.py backup
```

备份到指定目录：
```bash
python log_tools.py backup -d /path/to/backup
```

## 日志文件轮转

当日志文件达到配置的最大大小（默认10MB）时，系统会自动将其重命名为 `日志文件名.1`，并创建一个新的日志文件。当备份文件数量达到配置的最大数量（默认5个）时，最旧的备份文件会被删除。

例如，对于主日志文件，可能会有以下文件：
- pump_portal.log（当前日志文件）
- pump_portal.log.1（最近的一个备份）
- pump_portal.log.2
- pump_portal.log.3
- pump_portal.log.4
- pump_portal.log.5（最旧的备份）

## 故障排查

当系统出现错误时，可以查看错误日志获取详细信息：

```bash
python log_tools.py view -e
```

或直接查看错误日志文件：

```bash
cat logs/pump_portal_error.log
``` 