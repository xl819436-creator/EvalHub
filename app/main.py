"""EvalHub 应用组装入口：只创建 app、注册路由/异常/中间件。"""
from __future__ import annotations

from fastapi import FastAPI

from app.api import dataset, evaluation
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.middleware import RequestContextMiddleware

app = FastAPI(title=settings.app_name, version=settings.app_version)

register_error_handlers(app)
app.add_middleware(RequestContextMiddleware)
app.include_router(dataset.router)
app.include_router(evaluation.router)