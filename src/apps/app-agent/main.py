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
from beamlit.authentication import (RunClientWithCredentials,
                                    load_credentials_from_settings,
                                    new_client_with_credentials)
from beamlit.common.settings import get_settings, init, init_agent
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

from common.middlewares import AccessLogMiddleware, AddProcessTimeHeader

RUN_MODE = 'prod' if len(sys.argv) > 1 and sys.argv[1] == 'run' else 'dev'
agent = os.getenv("AGENT", "beamlit-agent")

main_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    is_main = __name__ == "main"
    if not is_main:
        init()

    settings = get_settings()
    credentials = load_credentials_from_settings(settings)
    client_config = RunClientWithCredentials(
        credentials=credentials,
        workspace=settings.workspace,
    )
    client = new_client_with_credentials(client_config)
    logger = getLogger(__name__)

    # Initialize the agent
    init_agent(client, destination=f"{os.getcwd()}/src/agents/beamlit.py")

    # Import the agent
    global main_agent
    main_agent = importlib.import_module(f"agents.{agent}.main")
    # Log the server is running
    if is_main:
        logger.info(f"Server running on http://{settings.host}:{settings.port}")
    yield

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

def main():
    init()
    settings = get_settings()
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level="critical")

if __name__ == "__main__":
    main()
