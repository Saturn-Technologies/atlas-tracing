from opentelemetry import propagators, trace
from opentelemetry.instrumentation.boto import BotoInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider


class Atlas:
    app = None
    tracer = None

    def __init__(self, app, service='atlas-api', sqlalchemy_engine=None, datadog_agent=None):
        self.app = app
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)
        if datadog_agent:
            from opentelemetry.exporter.datadog import DatadogExportSpanProcessor, \
                DatadogSpanExporter
            from opentelemetry.exporter.datadog.propagator import DatadogFormat
            exporter = DatadogSpanExporter(agent_url=datadog_agent, service=service)

            span_processor = DatadogExportSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

            # Optional: use Datadog format for propagation in distributed traces
            propagators.set_global_httptextformat(DatadogFormat())
        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        BotocoreInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        BotoInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        RedisInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
        if sqlalchemy_engine:
            SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine, service=service)
