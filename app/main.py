"""EvalHub 应用组装入口。"""
from __future__ import annotations

from fastapi import FastAPI

from app.api import datasets, evaluations
from app.core.config import settings
from app.core.database import Base, engine
from app.core.errors import register_error_handlers
from app.core.middleware import RequestContextMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)

register_error_handlers(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(datasets.router)
app.include_router(evaluations.router)