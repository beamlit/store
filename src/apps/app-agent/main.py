import asyncio
import filecmp
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

import common.bl_config as bl_config
from common.bl_logger import init as logger_init

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'
PACKAGE = os.getenv("PACKAGE", "app")

main_agent = None

async def init_app():
    import common.bl_auth as bl_auth
    import common.bl_generate as bl_generate
    import common.bl_register_request as bl_register_request

    global main_agent

    await bl_auth.auth()
    asyncio.create_task(bl_auth.auth_loop())

    # Init agent configuration
    bl_config.init_agent()


    destination = f"{os.path.dirname(__file__)}/agents/beamlit.py"
    if not os.path.exists(destination):
        bl_generate.run(destination)

    main_agent = importlib.import_module(".agents.main", package=PACKAGE)
    logger_init()

@asynccontextmanager
async def lifespan(app: FastAPI):
    bl_config.init(os.path.join(os.path.dirname(__file__), "agents"))
    bl_config.BL_CONFIG["type"] = "agent"

    if RUN_MODE == 'dev':
        import shutil
        if not os.path.exists("src/apps/app-agent/agents"):
            os.makedirs("src/apps/app-agent/agents")
        agent = os.getenv("AGENT", "langchain-external-providers") or "langchain-external-providers"
        cwd = os.getcwd()
        source_folder = f"{cwd}/src/agents/{agent}"
        destination_folder = f"{cwd}/src/apps/app-agent/agents"
        for file in os.listdir(source_folder):
            if (file.endswith(".py") or file.endswith(".yaml")) and (not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(f"{source_folder}/{file}", f"{destination_folder}/{file}")):
                shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")
    await init_app()
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CorrelationIdMiddleware)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/")
async def root(request: Request, background_tasks: BackgroundTasks):
    from common.bl_config import BL_CONFIG
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
        return JSONResponse(status_code=400, content=content)
    except Exception as e:
        content = {"error": f"Internal server error, {e}"}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)