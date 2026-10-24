"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from echomind.api.routes import build_router
from echomind.api.websocket import router as websocket_router


def create_app() -> FastAPI:
    app = FastAPI(title="EchoMind", version="0.1.0", description="Local-first speech intelligence prototype")
    app.include_router(build_router())
    app.include_router(websocket_router)
    return app


app = create_app()
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).with_name("static")),
    name="static",
)
