import asyncio
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager
from logging import getLogger

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from traceloop.sdk import Traceloop

from common.bl_auth import auth, auth_loop
from common.bl_config import BL_CONFIG, init, init_agent
from common.bl_instrumentation import (
    get_metrics_exporter,
    get_resource_attributes,
    get_span_exporter,
    instrument_app,
)
from common.bl_logger import init as logger_init
from common.middlewares import AccessLogMiddleware, AddProcessTimeHeader

RUN_MODE = "prod" if len(sys.argv) > 1 and sys.argv[1] == "run" else "dev"
BL_CONFIG["type"] = "agent"
init(os.path.dirname(__file__))
Traceloop.init(
    app_name=BL_CONFIG["name"],
    exporter=get_span_exporter(),
    metrics_exporter=get_metrics_exporter(),
    resource_attributes=get_resource_attributes(),
    should_enrich_metrics=os.getenv("ENRICHED_METRICS", "false") == "true",
)
agent = os.getenv("AGENT", "beamlit-agent")

main_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    is_main = __name__ == "main"
    if not is_main:
        logger_init()
        auth()

    logger = getLogger(__name__)

    # Initialize the agent
    init_agent()

    # Import the agent
    global main_agent
    main_agent = importlib.import_module(f"agents.{agent}.main")

    # Start the auth loop, that should retrieve JWT with client credentials
    asyncio.create_task(auth_loop())

    # Log the server is running
    if is_main:
        logger.info(f"Server running on http://{BL_CONFIG['host']}:{BL_CONFIG['port']}")
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(AddProcessTimeHeader)
app.add_middleware(AccessLogMiddleware)
instrument_app(app)  # Need to be called after the middleware


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/")
async def root(request: Request, background_tasks: BackgroundTasks):
    logger = getLogger(__name__)
    try:
        return await main_agent.main(request, background_tasks)
    except ValueError as e:
        content = {"error": str(e)}
        if RUN_MODE == "dev":
            content["traceback"] = str(traceback.format_exc())
        logger.error(f"{content}")
        return JSONResponse(status_code=400, content=content)
    except Exception as e:
        content = {"error": f"Internal server error, {e}"}
        if RUN_MODE == "dev":
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)


def main():
    logger_init()
    auth()
    uvicorn.run(
        "main:app",
        host=BL_CONFIG["host"],
        port=BL_CONFIG["port"],
        log_level="critical",
    )


if __name__ == "__main__":
    main()
