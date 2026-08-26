"""测试共享设施：内存 SQLite + 每测试重建表 + 依赖覆盖。

所有用到 app 的测试文件都应从这里拿 client，不要各自定义 engine/override，
否则多个文件会互相覆盖 dependency_overrides 导致 "no such table"。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    """SQLite 默认不启用外键约束，这里显式打开，让外键完整性测试生效。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def fresh_db():
    """每个测试独立：先建表，测完删表。"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    """Day 19：全测试套件禁止真实公网连接。

    只拦截“出站到公网”的 TCP 连接；本机回环（127.0.0.1 / ::1 / localhost）
    放行——Windows 上 asyncio 的 ProactorEventLoop 内部要用回环连接做唤醒，
    不能拦。任何测试试图连接公网（例如误调用收费 API）都会直接失败。

    MockProvider / httpx.MockTransport / TestClient 不经过真实网络，不受影响。
    """
    import socket

    original_connect = socket.socket.connect
    loopback_hosts = {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host in loopback_hosts:
            return original_connect(self, address, *args, **kwargs)
        raise OSError(
            "EvalHub 测试禁止真实公网连接，"
            "请使用 MockProvider / httpx.MockTransport，"
            f"被拦截的目标地址：{address}"
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)