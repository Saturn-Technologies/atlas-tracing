from fnmatch import fnmatch
from typing import List

from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.fastapi.version import __version__  # noqa


class ASGIMiddleware(OpenTelemetryMiddleware):
    def __init__(self, app, span_details_callback=None, ignored_paths: List[str] = None):
        super().__init__(app, span_details_callback=span_details_callback)
        self.ignored_paths = ignored_paths

    async def is_filtered(self, scope):
        return self.ignored_paths and any(fnmatch(scope['path'], p) for p in self.ignored_paths)

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        if await self.is_filtered(scope):
            response = await self.app(scope, receive, send)
        else:
            response = await super().__call__(scope, receive, send)
        return response
