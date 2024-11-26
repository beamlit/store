import asyncio
import filecmp
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager
from uuid import uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.bl_logger import init as logger_init

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'

main_function = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_function
    function = os.getenv("FUNCTION", "math")

    bl_config = importlib.import_module("common.bl_config")
    bl_config.BL_CONFIG["type"] = "function"
    bl_config.init(os.path.dirname(__file__))

    bl_auth = importlib.import_module("common.bl_auth")
    await bl_auth.auth()
    asyncio.create_task(bl_auth.auth_loop())
    logger_init()

    main_function = importlib.import_module(f"functions.{function}.main")
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CorrelationIdMiddleware, header_name="x-beamlit-request-id", generator=lambda: str(uuid4()))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/")
async def root(request: Request):
    try:
        body = await request.json()
        result = await main_function.main(body)
        return {"result": result}
    except ValueError as e:
        content = {"error": str(e)}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=400, content=content)
    except Exception as e:
        content = {"error": f"Internal server error, {e}"}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)
