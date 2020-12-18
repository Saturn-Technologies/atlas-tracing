from fnmatch import fnmatch
from functools import wraps
from typing import List

from opentelemetry import context, propagators, trace
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware, set_status_code, \
    collect_request_attributes, carrier_getter
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
            return await self.app(scope, receive, send)

        token = context.attach(propagators.extract(carrier_getter, scope))
        span_name, additional_attributes = self.span_details_callback(scope)

        try:
            with self.tracer.start_as_current_span(
                    span_name + " asgi", kind=trace.SpanKind.SERVER,
            ) as span:
                if span.is_recording():
                    attributes = collect_request_attributes(scope)
                    attributes.update(additional_attributes)
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                @wraps(receive)
                async def wrapped_receive():
                    with self.tracer.start_as_current_span(
                            span_name + " asgi." + scope["type"] + ".receive"
                    ) as receive_span:
                        message = await receive()
                        if receive_span.is_recording():
                            if message["type"] == "websocket.receive":
                                set_status_code(receive_span, 200)
                            receive_span.set_attribute("type", message["type"])
                    return message

                @wraps(send)
                async def wrapped_send(message):
                    with self.tracer.start_as_current_span(
                            span_name + " asgi." + scope["type"] + ".send"
                    ) as send_span:
                        if send_span.is_recording():
                            if message["type"] == "http.response.start":
                                status_code = message["status"]
                                set_status_code(send_span, status_code)
                                set_status_code(span, status_code)

                        elif message["type"] == "websocket.send":
                            set_status_code(send_span, 200)
                            set_status_code(span, 200)
                        send_span.set_attribute("type", message["type"])
                        await send(message)

                await self.app(scope, wrapped_receive, wrapped_send)
        finally:
            context.detach(token)
