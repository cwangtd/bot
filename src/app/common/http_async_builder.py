import httpx
from httpx import Response, Timeout

from app.common.logger_common import logger, log_exception

# Cloned from httpx._config.DEFAULT_TIMEOUT_CONFIG
DEFAULT_TIMEOUT = httpx.Timeout(timeout=5.0)
# No read timeout, and nothing to write actually
EXTENDED_TIMEOUT = httpx.Timeout(connect=300.0, read=None, write=10.0, pool=None)


class HttpAsyncBuilder:
    def __init__(self, url: str, tag: str = 'NoTag'):
        self._url: str = url
        self._tag: str = tag
        self._headers: dict | None = None
        self._payload: dict | None = None
        self._follow_redirects: bool = False

    def set_headers(self, headers: dict):
        self._headers = headers
        return self

    def set_payload(self, payload: dict):
        self._payload = payload
        return self

    def enable_follow_redirects(self):
        self._follow_redirects = True
        return self

    async def execute(self, timeout: Timeout = DEFAULT_TIMEOUT) -> Response:
        status_code = -1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self._payload is None:
                    method = 'AsyncGET'
                    response = await client.get(
                        self._url, headers=self._headers, follow_redirects=self._follow_redirects
                    )
                else:
                    method = 'AsyncPOST'
                    response = await client.post(
                        self._url, headers=self._headers, data=self._payload
                    )

            status_code = response.status_code
            response.raise_for_status()

            if self._tag is not None:
                logger.info(
                    ' | '.join([
                        self._tag,
                        method,
                        f'{response.elapsed.total_seconds():.3f}s',
                        self._url
                    ])
                )

            return response

        except Exception as e:
            log_exception(f'{self._tag} | {status_code} | {self._url}')
            return Response(status_code=500, text=str(e))
