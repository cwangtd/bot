import logging
import os
from contextvars import ContextVar

from pydantic import BaseModel
from pythonjsonlogger import jsonlogger


class LogConst:
    LOGGER_MAIN_TAG: str = 'main.app'
    LOGGER_FILENAME: str = 'app.log'
    LOGGER_MAIN_FORMATTER: str = 'formatter0'
    LOGGER_MAIN_HANDLER: str = 'handler0'

    GCP_RENAME_FIELDS = {
        'asctime': '@timestamp',
        'version': '@version',
        'name': 'logger_name',
        'thread': 'thread_name',
        'levelno': 'level_value',
        # For Cloud Run Log Explorer
        'levelname': 'severity',
        'trace_id': 'logging.googleapis.com/trace',
        'span_id': 'logging.googleapis.com/spanId',
    }

    STATIC_IS_JSON_LOG: ContextVar[bool] = ContextVar('is_json_log', default=True)


class AppFilter(logging.Filter):
    def filter(self, record):
        from app.common.middlewares import get_trace_id, get_span_id
        record.trace_id = get_trace_id()
        record.span_id = get_span_id()
        return True


class LogConfigHandler(BaseModel):
    version: int = 1  # Required
    disable_existing_loggers: bool = True  # TODO: find out what this does

    formatters: dict = {}
    handlers: dict = {}
    loggers: dict = {}
    filters: dict = {
        'app': {
            '()': 'app.common.logger_config.AppFilter',
        },
    }

    # Formats:
    #   -- JSON --
    #   just: %(levelname)s %(asctime)s %(name)s %(thread)d %(trace_id)s %(span_id)s %(message)s
    #   -- NON-JSON --
    #   local: %(levelname)s %(asctime)s | %(message)s
    #   server: %(levelname)s %(asctime)s %(name)s %(thread)d %(trace_id)s %(span_id)s | %(message)s
    #
    def __init__(
            self,
            # Default values of level, format, log_in_json are for local development.
            _level: str = 'DEBUG',
            _format: str = '%(levelname)s %(asctime)s | %(message)s',
            _log_in_json: bool = False,
            # Path only matters if _log_in_json is True.
            _path: str = '/opt/logs',
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.loggers[LogConst.LOGGER_MAIN_TAG] = {
            'handlers': [LogConst.LOGGER_MAIN_HANDLER],
            'level': getattr(logging, _level.upper())
        }

        if _log_in_json:
            self.formatters[LogConst.LOGGER_MAIN_FORMATTER] = {
                '()': jsonlogger.JsonFormatter,
                'fmt': _format,
                'rename_fields': LogConst.GCP_RENAME_FIELDS,  # TODO: how about AWS?
            }
        else:
            self.formatters[LogConst.LOGGER_MAIN_FORMATTER] = {
                '()': 'uvicorn.logging.DefaultFormatter',
                'fmt': _format,
            }

        if _path and len(_path) > 0:
            self.handlers[LogConst.LOGGER_MAIN_HANDLER] = {
                'formatter': LogConst.LOGGER_MAIN_FORMATTER,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': f'{_path}/{LogConst.LOGGER_FILENAME}',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'filters': ['app'],
            }
            os.makedirs(_path, exist_ok=True)
        else:
            self.handlers[LogConst.LOGGER_MAIN_HANDLER] = {
                "formatter": LogConst.LOGGER_MAIN_FORMATTER,
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "filters": ['app'],
            }

        LogConst.STATIC_IS_JSON_LOG.set(_log_in_json)
