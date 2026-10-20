import sys
from pathlib import Path

# Admite uvicorn backend.app:app y app:app desde backend/.
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.exceptions import PipelineError
from backend.api.adaptation import router as adaptation_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.exception_handler(PipelineError)
async def pipeline_error_handler(request: Request, error: PipelineError):
    return JSONResponse(status_code=error.status_code,
                        content={"detail": {"etapa": error.etapa, "mensaje": str(error)}})


@app.get(f"{settings.api_prefix}/health")
def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


app.include_router(
    adaptation_router,
    prefix=settings.api_prefix,
)
