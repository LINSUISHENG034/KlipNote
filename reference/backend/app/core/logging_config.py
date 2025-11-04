import logging
import logging.handlers
from pathlib import Path
import structlog

def configure_logging(settings_obj) -> None:
    """配置完整的日志系统"""
    log_dir = Path(settings_obj.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings_obj.LOG_LEVEL.upper(), logging.INFO)

    shared_processors: list[structlog.Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 创建处理器
    console_handler = logging.StreamHandler()
    if settings_obj.ENVIRONMENT == "local" and settings_obj.LOG_FORMAT == "console":
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    console_handler.setFormatter(formatter)

    log_file = log_dir / "audioalchemist.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=settings_obj.LOG_FILE_MAX_SIZE * 1024 * 1024,
        backupCount=settings_obj.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    ))

    error_log_file = log_dir / "audioalchemist_error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_log_file,
        maxBytes=settings_obj.LOG_FILE_MAX_SIZE * 1024 * 1024,
        backupCount=settings_obj.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    ))

    # 获取根记录器并应用配置
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # 清除现有处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.setLevel(log_level)

    # 抑制第三方库的日志
    for logger_name in ["multipart", "uvicorn.access", "httpx", "urllib3", "requests", "transformers", "torch"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # 确保Celery的日志级别与应用一致
    logging.getLogger("celery").setLevel(log_level)

    logger = structlog.get_logger("audio_alchemist")
    logger.info("Structured logging configured", log_level=settings_obj.LOG_LEVEL)
