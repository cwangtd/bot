import time
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

from app.common.logger_common import logger, to_elapsed_seconds

DEFAULT_CTX_VALUE = 'N/A'
TRACE_ID_CTX_KEY = 'X-B3-TraceId'
SPAN_ID_CTX_KEY = 'X-B3-SpanId'

_trace_id_ctx_var: ContextVar[str] = ContextVar(TRACE_ID_CTX_KEY, default=DEFAULT_CTX_VALUE)
_span_id_ctx_var: ContextVar[str] = ContextVar(SPAN_ID_CTX_KEY, default=DEFAULT_CTX_VALUE)


def get_trace_id() -> str:
    return _trace_id_ctx_var.get()


def get_span_id() -> str:
    return _span_id_ctx_var.get()


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start = time.perf_counter()
        key = f'{request.method} {request.url.path}?{request.url.query}'
        # TODO: dynamic for each app
        log_it = request.url.path.startswith('/api/v3/image')
        if log_it:
            logger.info(f'Request {key}')

        trace_id = _trace_id_ctx_var.set(request.headers.get(TRACE_ID_CTX_KEY, DEFAULT_CTX_VALUE))
        span_id = _span_id_ctx_var.set(request.headers.get(SPAN_ID_CTX_KEY, DEFAULT_CTX_VALUE))

        response = await call_next(request)
        response.headers[TRACE_ID_CTX_KEY] = get_trace_id()
        response.headers[SPAN_ID_CTX_KEY] = get_span_id()

        _trace_id_ctx_var.reset(trace_id)
        _span_id_ctx_var.reset(span_id)

        if log_it:
            elapsed = to_elapsed_seconds(time.perf_counter() - start)
            logger.info(f'Response {key} | {response.status_code} | {elapsed}')
        return response
