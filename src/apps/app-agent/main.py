import asyncio
import filecmp
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.bl_logger import init as logger_init

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'
PACKAGE = os.getenv("PACKAGE", "app")

main_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_agent
    if RUN_MODE == 'dev':
        import shutil

        if not os.path.exists("src/apps/app-agent/agents"):
            os.makedirs("src/apps/app-agent/agents")
        agent = os.getenv("AGENT", "langchain-chat-completions") or "langchain-chat-completions"
        cwd = os.getcwd()
        source_folder = f"{cwd}/src/agents/{agent}"
        destination_folder = f"{cwd}/src/apps/app-agent/agents"
        for file in os.listdir(source_folder):
            if (file.endswith(".py") or file.endswith(".yaml")) and (not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(f"{source_folder}/{file}", f"{destination_folder}/{file}")):
                shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")

    bl_config = importlib.import_module("common.bl_config", package=PACKAGE)
    bl_config.init(os.path.join(os.path.dirname(__file__), "agents"))
    bl_auth = importlib.import_module("common.bl_auth", package=PACKAGE)
    await bl_auth.auth()
    asyncio.create_task(bl_auth.auth_loop())
    bl_generate_functions = importlib.import_module("common.bl_generate_functions", package=PACKAGE)
    destination = f"{os.path.dirname(__file__)}/agents/beamlit.py"
    if not os.path.exists(destination):
        bl_generate_functions.run(destination)
    main_agent = importlib.import_module(".agents.main", package=PACKAGE)
    logger_init()
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/")
async def root(request: Request):
    try:
        return JSONResponse(await main_agent.main(request))
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