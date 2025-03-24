import logging
import os
from logging.config import dictConfig

from app.common.logger_config import LogConfigHandler, LogConst
from app.utils.lrucache import get_settings

settings = get_settings()

if settings.log_path:
    os.makedirs(os.path.dirname(settings.log_path), exist_ok=True)

dictConfig(
    LogConfigHandler(
        _level=settings.log_level,
        _format=settings.log_format,
        _log_in_json=settings.log_in_json,
        _path=settings.log_path,
    ).model_dump()
)

"""
This will be the first line of logging in the application. Logger starts taking action at this point after 
initialization of LogConfigHandler.
"""
logger = logging.getLogger('main.app')
logger.info(f'App initializing | {settings.model_dump()}')
