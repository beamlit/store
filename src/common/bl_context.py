from opentelemetry import trace


class Context:
    _tracer: trace.Tracer | None = None

    def __init__(self, tracer: trace.Tracer):
        Context._tracer = tracer

    @staticmethod
    def get_tracer() -> trace.Tracer:
        if Context._tracer is None:
            raise Exception("Tracer is not initialized")
        return Context._tracer
