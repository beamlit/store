import asyncio
import filecmp
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'
PACKAGE = os.getenv("PACKAGE", "app")

main_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_agent
    if RUN_MODE == 'dev':
        import shutil

        if not os.path.exists("apps/app-agent/agents"):
            os.makedirs("apps/app-agent/agents")
        agent = os.getenv("AGENT", "langchain-chat-completions") or "langchain-chat-completions"
        cwd = os.getcwd()
        source_folder = f"{cwd}/agents/{agent}"
        destination_folder = f"{cwd}/apps/app-agent/agents"
        for file in os.listdir(source_folder):
            if (file.endswith(".py") or file.endswith(".yaml")) and (not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(f"{source_folder}/{file}", f"{destination_folder}/{file}")):
                shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")

    bl_config = importlib.import_module(".agents.bl_config", package=PACKAGE)
    bl_config.init()
    bl_auth = importlib.import_module(".agents.bl_auth", package=PACKAGE)
    await bl_auth.auth()
    asyncio.create_task(bl_auth.auth_loop())
    bl_generate_functions = importlib.import_module(".agents.bl_generate_functions", package=PACKAGE)
    destination = f"{"/".join(bl_generate_functions.__file__.split("/")[0:-1])}/beamlit.py"
    if not os.path.exists(destination):
        bl_generate_functions.run(f"{"/".join(bl_generate_functions.__file__.split("/")[0:-1])}/beamlit.py")
    main_agent = importlib.import_module(".agents.main", package=PACKAGE)

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
    except Exception:
        content = {"error": "Internal server error"}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)
