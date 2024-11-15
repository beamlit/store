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

main_function = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_function
    if RUN_MODE == 'dev':
        import shutil

        if not os.path.exists("src/apps/app-function/functions"):
            os.makedirs("src/apps/app-function/functions")
        function = os.getenv("TOOL", "math")
        cwd = os.getcwd()
        source_folder = f"{cwd}/src/functions/{function}"
        destination_folder = f"{cwd}/src/apps/app-function/functions"
        for file in os.listdir(source_folder):
            if file.endswith(".py") and (not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(f"{source_folder}/{file}", f"{destination_folder}/{file}")):
                shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")

    bl_config = importlib.import_module("common.bl_config", package=PACKAGE)
    bl_config.init(os.path.join(os.path.dirname(__file__), "functions"))

    bl_auth = importlib.import_module("common.bl_auth", package=PACKAGE)
    await bl_auth.auth()
    asyncio.create_task(bl_auth.auth_loop())
    logger_init()

    main_function = importlib.import_module(".functions.main", package=PACKAGE)
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

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
