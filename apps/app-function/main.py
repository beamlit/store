import filecmp
import importlib
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logger import init as logger_init

RUN_MODE = 'prod' if sys.argv[1] == 'run' else 'dev'
PACKAGE = os.getenv("PACKAGE", "app")

main_function = None
if RUN_MODE == 'prod':
    main_function = importlib.import_module(".functions", package=PACKAGE)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_function
    if RUN_MODE == 'dev':
        import shutil

        if not os.path.exists("apps/app-function/functions"):
            os.makedirs("apps/app-function/functions")
        function = os.getenv("TOOL", "math")
        cwd = os.getcwd()
        source_folder = f"{cwd}/functions/{function}"
        destination_folder = f"{cwd}/apps/app-function/functions"
        for file in os.listdir(source_folder):
            if file.endswith(".py") and (not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(f"{source_folder}/{file}", f"{destination_folder}/{file}")):
                shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")
        main_function = importlib.import_module(".functions", package=PACKAGE)

    logger_init()

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
    except Exception:
        content = {"error": "Internal server error"}
        if RUN_MODE == 'dev':
            content["traceback"] = str(traceback.format_exc())
        return JSONResponse(status_code=500, content=content)
