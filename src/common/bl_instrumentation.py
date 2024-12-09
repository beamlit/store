from typing import Any
from fastapi import FastAPI
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from typing_extensions import Dict
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
from common.bl_config import BL_CONFIG

tracer: trace.Tracer | None = None


def get_tracer() -> trace.Tracer:
    if tracer is None:
        raise Exception("Tracer is not initialized")
    return tracer


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


def instrument_fast_api(app: FastAPI):
    global tracer
    resource = Resource.create(
        {
            "service.name": BL_CONFIG["name"],
            "service.namespace": BL_CONFIG["workspace"],
            "service.workspace": BL_CONFIG["workspace"],
        }
    )
    # Set up the TracerProvider
    provider = TracerProvider(resource=resource)
    tracer = provider.get_tracer(__name__)
    span_processor = BatchSpanProcessor(get_span_exporter())
    provider.add_span_processor(span_processor)
    FastAPIInstrumentor.instrument_app(app=app, tracer_provider=provider)  # type: ignore
    HTTPXClientInstrumentor().instrument()  # type: ignore
