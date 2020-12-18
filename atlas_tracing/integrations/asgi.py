from fnmatch import fnmatch
from typing import List

from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware


class ASGIMiddleware(OpenTelemetryMiddleware):
    def __init__(self, app, span_details_callback=None, ignored_paths: List[str] = None):
        super().__init__(app, span_details_callback=span_details_callback)
        self.ignored_paths = ignored_paths

    async def __call__(self, scope, receive, send):
        if self.ignored_paths and any(fnmatch(scope.get('path', None), p) for p in self.ignored_paths):
            return await self.app(scope, receive, send)
        else:
            return await super().__call__(scope, receive, send)
