from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.base import router as base_router


def create_app() -> FastAPI:
    app = FastAPI(root_path="/api/v1")
    ## = FastAPI(root_path="/")
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(base_router, prefix="/base", tags=["Base APIs"])
    ##app.include_router(base_router, prefix="", tags=["Base APIs"])
    return app
