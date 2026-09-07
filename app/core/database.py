"""SQLAlchemy 2.x 引擎、会话与 Base。"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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


def ensure_schema() -> None:
    """创建表，并为 v0.1.0 已存在的 SQLite 数据库补齐新列。"""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        dataset_columns = {column["name"] for column in inspect(engine).get_columns("datasets")}
        if "samples" not in dataset_columns:
            connection.execute(text("ALTER TABLE datasets ADD COLUMN samples JSON"))
        job_columns = {column["name"] for column in inspect(engine).get_columns("evaluation_jobs")}
        if "temperature" not in job_columns:
            connection.execute(
                text("ALTER TABLE evaluation_jobs ADD COLUMN temperature FLOAT NOT NULL DEFAULT 0.7")
            )
        run_columns = {column["name"] for column in inspect(engine).get_columns("evaluation_runs")}
        for column_name in ("input", "expected", "actual", "reason"):
            if column_name not in run_columns:
                connection.execute(
                    text(f"ALTER TABLE evaluation_runs ADD COLUMN {column_name} TEXT")
                )


def get_db():
    """FastAPI 依赖：每请求一个 Session，用后必关。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
