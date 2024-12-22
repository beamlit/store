from logging import getLogger

from starlette.middleware.base import BaseHTTPMiddleware


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger = getLogger(__name__)
        response = await call_next(request)
        process_time = response.headers.get("X-Process-Time")
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {process_time}ms"
        )
        return response
