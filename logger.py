"""
结构化日志系统

替代 print()，支持控制台输出 + 文件日志 + 自动轮转
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """日志管理器"""

    _instances: dict[str, logging.Logger] = {}
    _initialized = False

    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
        """
        获取或创建 logger

        Args:
            name: logger 名称（通常用 __name__）
            log_file: 日志文件路径（None = 不写文件）
            level: DEBUG / INFO / WARNING / ERROR
        """
        if name in cls._instances:
            return cls._instances[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 避免重复添加 handler
        if logger.handlers:
            return logger

        # 控制台 Handler（彩色输出在终端，GBK 安全） - 全部使用 INFO 级别
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)

        # 精简格式：仅显示消息（调用者负责加前缀）
        formatter = logging.Formatter("%(message)s")
        console.setFormatter(formatter)
        logger.addHandler(console)

        # 文件 Handler（仅在指定 log_file 时添加）
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(log_path),
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        cls._instances[name] = logger
        return logger

    @classmethod
    def get_file_logger(cls, name: str, log_file: str) -> logging.Logger:
        """获取同时写文件和终端的 logger"""
        return cls.get_logger(name, log_file=log_file)


# 便捷函数
def get_logger(name: str = __name__, log_file: Optional[str] = None) -> logging.Logger:
    return Logger.get_logger(name, log_file=log_file)
