from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.candidate import router as candidate_router
from app.api.routes.cv import router as cv_router
from app.api.routes.applications import router as applications_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.settings import router as settings_router


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.services.persistence import bootstrap_persistence

    result = bootstrap_persistence()
    _app.state.persistence = result
    yield


app = FastAPI(
    title="AgenteCV",
    description="AI agent for CV optimization and job applications",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(candidate_router)
app.include_router(cv_router)
app.include_router(applications_router)
app.include_router(jobs_router)
app.include_router(settings_router)


@app.get("/", include_in_schema=False)
def landing():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/cv", include_in_schema=False)
def cv_page():
    return FileResponse(FRONTEND_DIR / "cv.html")


@app.get("/opportunities", include_in_schema=False)
def opportunities_page():
    return FileResponse(FRONTEND_DIR / "opportunities.html")


@app.get("/applications", include_in_schema=False)
def applications_page():
    return FileResponse(FRONTEND_DIR / "applications.html")


@app.get("/settings", include_in_schema=False)
def settings_page():
    return FileResponse(FRONTEND_DIR / "settings.html")


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
