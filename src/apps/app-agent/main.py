import asyncio
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager
from logging import getLogger
from uuid import uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

from common.bl_auth import auth, auth_loop
from common.bl_config import BL_CONFIG, init, init_agent
from common.bl_logger import init as logger_init

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'
BL_CONFIG["type"] = "agent"
agent = os.getenv("AGENT", "beamlit-agent")


init(os.path.dirname(__file__))
auth()
init_agent()
logger_init()
main_agent = importlib.import_module(f"agents.{agent}.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(auth_loop())
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CorrelationIdMiddleware, header_name="x-beamlit-request-id", generator=lambda: str(uuid4()))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/")
async def root(request: Request, background_tasks: BackgroundTasks):
    logger = getLogger(__name__)
    try:
        chain = BL_CONFIG.get('agent_chain') or []
        functions = BL_CONFIG.get('agent_functions') or []
        if len(chain) == 0 and len(functions) == 0:
            content = {"error": "No agent chain or functions configured"}
            return JSONResponse(status_code=400, content=content)
        return await main_agent.main(request, background_tasks)
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
