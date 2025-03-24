import asyncio
import functools
import inspect
import logging
import sys
import time
import traceback
from contextvars import ContextVar

from app.common.logger_config import LogConst

logger = logging.getLogger('main.app')


def log_exception(tag: str, level_func: callable = logger.error):
    segments = [tag]

    stacks = inspect.stack()[1:]
    for frame in stacks:
        frame: inspect.FrameInfo
        if '/app/' in frame.filename:
            app_file = frame.filename.split('/app/')[-1]
            segments.append(f'{app_file}::{frame.function}::{frame.lineno}')
        else:
            break

    exc_type, exc_value, _ = sys.exc_info()
    was_exception = exc_type is not None
    if was_exception:
        segments.insert(1, f'{exc_type.__module__}.{exc_type.__name__}')
        segments.insert(2, str(exc_value) if exc_value else 'N/A')

    level_func(' | '.join(segments))

    if was_exception and not LogConst.STATIC_IS_JSON_LOG.get():
        level_func(traceback.format_exc().strip())


def to_iso_time(t: float) -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(t))


def to_elapsed_seconds(t: float, fraction_digits: int = 3) -> str:
    return f'elapsed {round(t, fraction_digits)}s'


def timed_log(
        tag: str, start_ts: float,
        extra_data: str = None,
        level_func: callable = None,
        slow_warning_threshold: float = -1.0
):
    elapsed = time.perf_counter() - start_ts
    elapsed_str = to_elapsed_seconds(elapsed)
    line = f'{tag} | {elapsed_str}' if extra_data is None else f'{tag} | {elapsed_str} | {extra_data}'

    if level_func:
        level_func(line)
    elif slow_warning_threshold < 0:
        logger.error(line)
    elif elapsed > slow_warning_threshold:
        logger.warning(line)


def timed(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = await func(*args, **kwargs)
        timed_log(func.__name__, start_ts, level_func=logger.info)
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = func(*args, **kwargs)
        timed_log(func.__name__, start_ts, level_func=logger.info)
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def timed_plus(tag: str, level_func: callable):
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_ts = time.perf_counter()
            result = await func(*args, **kwargs)
            timed_log(tag, start_ts, level_func=level_func)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_ts = time.perf_counter()
            result = func(*args, **kwargs)
            timed_log(tag, start_ts, level_func=level_func)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class TimedContext:
    TIMED_CONTEXT_TAG = 'timed_ctx_tag'
    TIMED_CONTEXT_DEFAULT_VALUE = ''
    tag: ContextVar[str] = ContextVar(TIMED_CONTEXT_TAG, default=TIMED_CONTEXT_DEFAULT_VALUE)

    @staticmethod
    def log(data: str, level_func: callable = logger.info):
        level_func(f'{TimedContext.tag.get()} | {data}')


def timed_context(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = await func(*args, **kwargs)
        tag1 = TimedContext.tag.get()
        tag2 = kwargs.get('_alt_tag', func.__name__)
        timed_log(f'{tag1} | {tag2}', start_ts, level_func=logger.info)
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_ts = time.perf_counter()
        result = func(*args, **kwargs)
        tag1 = TimedContext.tag.get()
        tag2 = kwargs.get('_alt_tag', func.__name__)
        timed_log(f'{tag1} | {tag2}', start_ts, level_func=logger.info)
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
