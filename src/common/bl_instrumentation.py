from typing import Any
from fastapi import FastAPI
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from typing_extensions import Dict
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from common.bl_config import BL_CONFIG

tracer: trace.Tracer | None = None
meter: metrics.Meter | None = None


def get_tracer() -> trace.Tracer:
    if tracer is None:
        raise Exception("Tracer is not initialized")
    return tracer


def get_meter() -> metrics.Meter:
    if meter is None:
        raise Exception("Meter is not initialized")
    return meter


def get_resource_attributes() -> Dict[str, Any]:
    resources = Resource.create()
    resources_dict: Dict[str, Any] = {}
    for key in resources.attributes:
        resources_dict[key] = resources.attributes[key]
    resources_dict["workspace"] = BL_CONFIG["workspace"]
    resources_dict["service.name"] = BL_CONFIG["name"]
    return resources_dict


def get_metrics_exporter() -> OTLPMetricExporter:
    return OTLPMetricExporter()


def get_span_exporter() -> OTLPSpanExporter:
    return OTLPSpanExporter()


def instrument_app(app: FastAPI):
    global tracer
    global meter
    resource = Resource.create(
        {
            "service.name": BL_CONFIG["name"],
            "service.namespace": BL_CONFIG["workspace"],
            "service.workspace": BL_CONFIG["workspace"],
        }
    )
    # Set up the TracerProvider
    trace_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(get_span_exporter())
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)
    tracer = trace_provider.get_tracer(__name__)

    metrics_exporter = PeriodicExportingMetricReader(get_metrics_exporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[metrics_exporter])
    metrics.set_meter_provider(meter_provider)
    meter = meter_provider.get_meter(__name__)

    FastAPIInstrumentor.instrument_app(
        app=app, tracer_provider=trace_provider, meter_provider=meter_provider
    )  # type: ignore
    HTTPXClientInstrumentor().instrument(meter_provider=meter_provider)  # type: ignore
    LoggingInstrumentor(tracer_provider=trace_provider).instrument(
        set_logging_format=True
    )  # type: ignore
