import asyncio
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager
from logging import getLogger
from uuid import uuid4

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

from common.bl_auth import auth, auth_loop
from common.bl_config import BL_CONFIG, init
from common.bl_context import Context
from common.bl_instrumentation import instrument_fast_api, get_tracer
from common.bl_logger import init as logger_init
from common.middlewares import AccessLogMiddleware, AddProcessTimeHeader

RUN_MODE = "prod" if len(sys.argv) > 1 and sys.argv[1] == "run" else "dev"
BL_CONFIG["type"] = "function"
init(os.path.dirname(__file__))
function = os.getenv("FUNCTION", "math")


main_function = importlib.import_module(f"functions.{function}.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    is_main = __name__ == "main"
    if not is_main:
        logger_init()
        auth()

    logger = getLogger(__name__)

    # Import the function
    global main_function
    main_function = importlib.import_module(f"functions.{function}.main")

    # Start the auth loop, that should retrieve JWT with client credentials
    asyncio.create_task(auth_loop())

    # Log the server is running
    if is_main:
        logger.info(f"Server running on http://{BL_CONFIG['host']}:{BL_CONFIG['port']}")
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
instrument_fast_api(app)
app.add_middleware(
    CorrelationIdMiddleware,
    header_name="x-beamlit-request-id",
    generator=lambda: str(uuid4()),
)
app.add_middleware(AddProcessTimeHeader)
app.add_middleware(AccessLogMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/")
async def root(request: Request, background_tasks: BackgroundTasks):
    logger = getLogger(__name__)
    try:
        body = await request.json()
        return await main_function.main(
            Context(tracer=get_tracer()),
            request,
            body,
            background_tasks=background_tasks,
        )
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
        "main:app", host=BL_CONFIG["host"], port=BL_CONFIG["port"], log_level="critical"
    )


if __name__ == "__main__":
    main()
