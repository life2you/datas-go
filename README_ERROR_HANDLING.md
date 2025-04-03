# 错误处理系统使用说明

本项目实现了完善的错误处理系统，包括错误日志记录、邮件通知和错误查看工具，帮助您及时发现和处理问题。

## 系统特点

- **全局错误捕获**：捕获未处理的异常，确保程序不会静默失败
- **详细错误日志**：记录完整的堆栈跟踪和错误上下文
- **邮件通知**：当发生严重错误时，可以自动发送邮件通知相关人员
- **错误装饰器**：通过简单的装饰器为函数添加错误处理和日志记录
- **错误查看工具**：提供命令行工具快速查看最近的错误

## 配置项

在 `.env` 文件中可以配置以下错误处理相关参数：

```
# 错误通知配置
# 是否启用错误通知邮件 (true/false)
ERROR_EMAIL_ENABLED=false
# SMTP服务器
ERROR_EMAIL_HOST=smtp.example.com
# SMTP端口
ERROR_EMAIL_PORT=587
# SMTP用户名
ERROR_EMAIL_USER=your-email@example.com
# SMTP密码
ERROR_EMAIL_PASSWORD=your-password
# 发件人地址（留空则使用EMAIL_USER）
ERROR_EMAIL_FROM=
# 收件人地址，多个地址用逗号分隔
ERROR_EMAIL_TO=admin@example.com
# 邮件主题前缀
ERROR_EMAIL_SUBJECT_PREFIX=[PUMP-ERROR]
```

## 在代码中使用错误处理

### 全局错误捕获

全局错误捕获已在应用程序启动时通过 `setup_error_handling()` 自动设置，无需额外配置。

### 装饰器使用

你可以使用装饰器为函数添加错误处理功能：

```python
from src.utils.error_handler import error_handler, async_error_handler

# 为普通函数添加错误处理
@error_handler
def some_function():
    # 函数内容
    pass

# 为异步函数添加错误处理
@async_error_handler
async def some_async_function():
    # 函数内容
    pass
```

当函数执行出错时，系统将：
1. 记录详细的错误信息到错误日志
2. 如果配置了邮件通知，发送错误通知邮件
3. 重新抛出异常，允许调用者决定如何继续处理

### 手动记录错误

你也可以手动记录错误：

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    # 可能出错的代码
    pass
except Exception as e:
    logger.error(f"发生错误: {str(e)}", exc_info=True)
    # 处理错误
```

## 使用错误查看工具

项目提供了一个错误查看工具 `check_errors.py`，可以方便地查看最近发生的错误：

### 显示最近的错误

显示最近10条错误（默认）：
```bash
python check_errors.py
```

显示指定数量的错误：
```bash
python check_errors.py -n 5
```

### 显示时间范围内的错误

显示最近24小时内的错误：
```bash
python check_errors.py -t 24
```

### 显示格式控制

显示完整的错误信息：
```bash
python check_errors.py -f
```

只显示错误摘要：
```bash
python check_errors.py -s
```

## 错误邮件通知

当启用邮件通知（`ERROR_EMAIL_ENABLED=true`）时，系统会在发生错误时自动发送邮件通知。

邮件内容包括：
- 错误类型和时间
- 详细的错误消息
- 完整的堆栈跟踪

### 配置SMTP服务器

根据你使用的邮件服务商，配置相应的SMTP服务器信息：

常见邮件服务商的SMTP配置：
- Gmail: `smtp.gmail.com:587`
- Outlook/Hotmail: `smtp.office365.com:587`
- QQ邮箱: `smtp.qq.com:587`
- 163邮箱: `smtp.163.com:25`

**注意**: 如果使用Gmail或其他服务，可能需要生成应用专用密码而不是使用普通密码。

## 常见问题排查

### 错误通知邮件未发送

1. 检查 `ERROR_EMAIL_ENABLED` 是否设置为 `true`
2. 确认 SMTP 服务器配置是否正确
3. 检查邮箱凭据是否有效
4. 查看日志文件中是否有邮件发送失败的记录

### 查看当前错误日志

使用以下命令查看错误日志文件：

```bash
cat logs/pump_portal_error.log
```

或使用错误查看工具：

```bash
python check_errors.py -f
``` 