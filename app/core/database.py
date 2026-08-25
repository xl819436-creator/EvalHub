"""SQLAlchemy 2.x 引擎、会话与 Base。"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 数据库文件路径：优先读环境变量 EVALHUB_DB_PATH（Docker 数据卷需要），
# 默认使用项目 data/evalhub.db，保证本地行为不变。
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_DEFAULT_DATA_DIR.mkdir(exist_ok=True)
DB_PATH = Path(
    os.environ.get("EVALHUB_DB_PATH", str(_DEFAULT_DATA_DIR / "evalhub.db"))
)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖：每请求一个 Session，用后必关。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()