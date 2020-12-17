from opentelemetry import trace
from opentelemetry.instrumentation.boto import BotoInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)
from sqlalchemy.engine import Engine


class Atlas:
    app = None
    tracer = None

    def __init__(self, app, service='atlas-api'):
        self.tracer = trace.get_tracer(__name__)
        self.app = app
        trace.set_tracer_provider(TracerProvider())
        trace.get_tracer_provider().add_span_processor(
            SimpleExportSpanProcessor(ConsoleSpanExporter()))
        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        BotocoreInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        BotoInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        RedisInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        SQLAlchemyInstrumentor().instrument(engine=Engine, service=service)
