package logger

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/life2you/datas-go/configs"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

// 全局日志实例
var (
	Logger *zap.Logger
	Sugar  *zap.SugaredLogger
)

// Init 初始化日志系统
func Init(cfg *configs.LogConfig) {
	// 创建日志目录
	if cfg.Path != "" {
		logDir := filepath.Dir(cfg.Path)
		if err := os.MkdirAll(logDir, 0755); err != nil {
			panic(fmt.Errorf("创建日志目录失败: %w", err))
		}
	}

	// 解析日志级别
	level := parseLogLevel(cfg.Level)

	// 创建Encoder
	encoderConfig := zapcore.EncoderConfig{
		TimeKey:        "time",
		LevelKey:       "level",
		NameKey:        "logger",
		CallerKey:      "caller",
		FunctionKey:    zapcore.OmitKey,
		MessageKey:     "msg",
		StacktraceKey:  "stacktrace",
		LineEnding:     zapcore.DefaultLineEnding,
		EncodeLevel:    zapcore.CapitalLevelEncoder,
		EncodeTime:     zapcore.ISO8601TimeEncoder,
		EncodeDuration: zapcore.SecondsDurationEncoder,
		EncodeCaller:   zapcore.ShortCallerEncoder,
	}

	// 配置Encoder
	var encoder zapcore.Encoder
	if strings.ToLower(cfg.Format) == "json" {
		encoder = zapcore.NewJSONEncoder(encoderConfig)
	} else {
		encoder = zapcore.NewConsoleEncoder(encoderConfig)
	}

	// 配置输出
	var cores []zapcore.Core

	// 文件输出
	if cfg.Path != "" {
		// 配置日志轮转
		fileWriter := &lumberjack.Logger{
			Filename:   cfg.Path,
			MaxSize:    cfg.MaxSize,
			MaxBackups: cfg.MaxBackups,
			MaxAge:     cfg.MaxAge,
			Compress:   cfg.Compress,
			LocalTime:  true,
		}

		fileCore := zapcore.NewCore(
			encoder,
			zapcore.AddSync(fileWriter),
			level,
		)
		cores = append(cores, fileCore)
	}

	// 控制台输出
	if cfg.Stdout {
		consoleCore := zapcore.NewCore(
			encoder,
			zapcore.AddSync(os.Stdout),
			level,
		)
		cores = append(cores, consoleCore)
	}

	// 创建Logger
	core := zapcore.NewTee(cores...)
	logger := zap.New(core, zap.AddCaller(), zap.AddCallerSkip(1))

	// 替换全局Logger
	Logger = logger
	Sugar = logger.Sugar()

	// 替换全局zap logger
	zap.ReplaceGlobals(logger)
}

// Close 关闭日志系统
func Close() {
	if Logger != nil {
		Logger.Sync()
	}
}

// parseLogLevel 解析日志级别
func parseLogLevel(levelStr string) zapcore.Level {
	switch strings.ToLower(levelStr) {
	case "debug":
		return zapcore.DebugLevel
	case "info":
		return zapcore.InfoLevel
	case "warn", "warning":
		return zapcore.WarnLevel
	case "error":
		return zapcore.ErrorLevel
	case "dpanic":
		return zapcore.DPanicLevel
	case "panic":
		return zapcore.PanicLevel
	case "fatal":
		return zapcore.FatalLevel
	default:
		return zapcore.InfoLevel
	}
}

// Debug 输出调试日志
func Debug(msg string, fields ...zap.Field) {
	Logger.Debug(msg, fields...)
}

// Info 输出信息日志
func Info(msg string, fields ...zap.Field) {
	Logger.Info(msg, fields...)
}

// Warn 输出警告日志
func Warn(msg string, fields ...zap.Field) {
	Logger.Warn(msg, fields...)
}

// Error 输出错误日志
func Error(msg string, fields ...zap.Field) {
	Logger.Error(msg, fields...)
}

// Fatal 输出致命错误日志并退出程序
func Fatal(msg string, fields ...zap.Field) {
	Logger.Fatal(msg, fields...)
}

// Debugf 使用格式化字符串输出调试日志
func Debugf(format string, args ...interface{}) {
	Sugar.Debugf(format, args...)
}

// Infof 使用格式化字符串输出信息日志
func Infof(format string, args ...interface{}) {
	Sugar.Infof(format, args...)
}

// Warnf 使用格式化字符串输出警告日志
func Warnf(format string, args ...interface{}) {
	Sugar.Warnf(format, args...)
}

// Errorf 使用格式化字符串输出错误日志
func Errorf(format string, args ...interface{}) {
	Sugar.Errorf(format, args...)
}

// Fatalf 使用格式化字符串输出致命错误日志并退出程序
func Fatalf(format string, args ...interface{}) {
	Sugar.Fatalf(format, args...)
}

// With 返回一个带有字段的Logger
func With(fields ...zap.Field) *zap.Logger {
	return Logger.With(fields...)
}

// Withf 返回一个带有字段的SugaredLogger
func Withf(args ...interface{}) *zap.SugaredLogger {
	return Sugar.With(args...)
}
