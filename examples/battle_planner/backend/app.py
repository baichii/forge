"""Battle planner FastAPI app。"""

from __future__ import annotations

from battle_planner.backend.api.contexts import router as contexts_router
from battle_planner.backend.api.plans import router as plans_router
from battle_planner.backend.api.runs import router as runs_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """创建 battle planner 后端应用。"""

    app = FastAPI(title="Battle Planner Backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(plans_router)
    app.include_router(contexts_router)
    app.include_router(runs_router)
    return app


app = create_app()
