import inspect
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any

DEFAULT_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_FILE = os.getenv("APP_LOG_FILE", None)
DEFAULT_LOG_MAX_BYTES = int(os.getenv("APP_LOG_MAX_BYTES", "10485760"))
DEFAULT_LOG_BACKUP_COUNT = int(os.getenv("APP_LOG_BACKUP_COUNT", "5"))


def _get_level(level_str: str) -> int:
    level = getattr(logging, level_str, None)
    if isinstance(level, int):
        return level
    raise ValueError(f"Invalid log level: {level_str}")


def setup_logger(
    name: str,
    level: str = DEFAULT_LOG_LEVEL,
    log_file: str | None = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_LOG_MAX_BYTES,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
    fmt: str = "[%(asctime)s %(levelname)s %(name)s:%(lineno)d] %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    propagate: bool = False,
) -> logging.Logger:
    log_level = _get_level(level)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = propagate

    if not logger.handlers:
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            path = Path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(path), maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8", mode="w"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def _get_caller_logger() -> logging.Logger:
    frame = inspect.stack()[2]
    module = inspect.getmodule(frame[0])
    if module is None or not hasattr(module, "__name__"):
        name = "__main__"
    else:
        name = module.__name__
    return logging.getLogger(name)


def LOG_DEBUG(msg: str, *args: Any, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    # stacklevel=2, 表示跳过一层（LOG_DEBUG）再往上定位, 以正确显示调用位置
    logger.debug(msg, *args, stacklevel=2, **kwargs)


def LOG_INFO(msg: str, *args: Any, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    logger.info(msg, *args, stacklevel=2, **kwargs)


def LOG_WARNING(msg: str, *args: Any, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    logger.warning(msg, *args, stacklevel=2, **kwargs)


def LOG_ERROR(msg: str, *args: Any, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    logger.error(msg, *args, stacklevel=2, **kwargs)


def LOG_CRITICAL(msg: str, *args: Any, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    logger.critical(msg, *args, stacklevel=2, **kwargs)
