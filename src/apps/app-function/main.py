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
from beamlit.common.settings import get_settings, init
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

from common.middlewares import AccessLogMiddleware, AddProcessTimeHeader

RUN_MODE = 'prod' if len(sys.argv) > 1 and sys.argv[1] == 'run' else 'dev'

function = os.getenv("FUNCTION", "math")


main_function = importlib.import_module(f"functions.{function}.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        is_main = __name__ == "main"
        if not is_main:
            init()

        settings = get_settings()
        logger = getLogger(__name__)

        # Import the function
        global main_function
        main_function = importlib.import_module(f"functions.{function}.main")

        # Log the server is running
        if is_main:
            logger.info(f"Server running on http://{settings.host}:{settings.port}")
        yield
    except Exception as e:
        logger = getLogger(__name__)
        logger.error(f"Error initializing function: {e}")
        raise e

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CorrelationIdMiddleware, header_name="x-beamlit-request-id", generator=lambda: str(uuid4()))
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
        return await main_function.main(request, body, background_tasks=background_tasks)
    except ValueError as e:
        content = {"error": str(e)}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        logger.error(f"{content}")
        return JSONResponse(status_code=400, content=content)
    except Exception as e:
        content = {"error": f"Internal server error, {e}"}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)

def main():
    settings = init()
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level="critical")

if __name__ == "__main__":
    main()