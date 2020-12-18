from typing import List

from opentelemetry import trace
from opentelemetry.instrumentation.boto import BotoInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider

from atlas_tracing.integrations.fastapi import AtlasFastAPIInstrumentor


class Atlas:
    app = None
    tracer = None

    def __init__(self, app, service='atlas-api', sqlalchemy_engine=None, datadog_agent=None,
                 span_callback=None, ignored_paths: List[str] = None, sql_service=None):
        self.app = app
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)
        if datadog_agent:
            from opentelemetry.exporter.datadog import DatadogExportSpanProcessor, \
                DatadogSpanExporter
            exporter = DatadogSpanExporter(agent_url=datadog_agent, service=service)

            span_processor = DatadogExportSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

        AtlasFastAPIInstrumentor.instrument_app(app, span_callback=span_callback,
                                                ignored_paths=ignored_paths)
        RequestsInstrumentor().instrument()
        BotocoreInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        BotoInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        RedisInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        if sqlalchemy_engine:
            sqlalch_service_name = service if not sql_service else sql_service
            SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine,
                                                service=sqlalch_service_name)
