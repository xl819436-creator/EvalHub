# 数据库决策记录（Day 18）

> 本文回答三个问题：为什么用 SQLite、事务边界在哪里、未来如何换成 PostgreSQL。
> 与代码对照：`app/core/database.py`（引擎/会话）、`app/models/*.py`（ORM）、`app/repositories/*.py`（Repository）、`app/services/evaluation_service.py`（业务状态）、`tests/conftest.py`（测试隔离）。

## 1. 为什么用 SQLite

| 考量 | 结论 |
|---|---|
| 零配置 | 标准库自带驱动，无需安装数据库服务，`create_engine` 一行即用 |
| 单文件 | 整个数据库就是 `data/evalhub.db` 一个文件，拷贝即备份，适合学习项目 |
| 测试友好 | 内存模式 `sqlite://` + `StaticPool`，每个测试独立建表/删表，速度快且不污染真实数据 |
| 与课程衔接 | Day 10 已用 SQLite 做过三张表 CRUD，概念可复用 |

代价（现阶段接受）：

- 并发写弱：同一时刻只能一个写事务，多进程写会报 `database is locked`。EvalHub 目前是单进程 API 服务，够用。
- SQLite 默认**不开启外键约束**，需要每次连接执行 `PRAGMA foreign_keys=ON`（见 `tests/conftest.py` 的 `_enable_sqlite_fk`）。生产库（PostgreSQL/MySQL）默认开启，这里提前显式打开是为了让外键完整性测试真实有效。

## 2. 事务边界在哪里

分层原则（Day 17 拆分 + Day 18 实作）：

- **Repository 层**：只做数据库操作，负责 `commit` / `rollback`。例如 `JobRepository.create_job()` 内部 `add → commit → refresh`。
- **Service 层**：管业务规则，不碰 SQL。例如 `EvaluationService.transition()` 先校验 `ALLOWED_TRANSITIONS`（`pending→running→completed/failed`，禁止 `running→pending`），校验通过才调用 Repository。
- **路由层**：通过 `Depends(get_db)` 拿到 Session 后交给 Service，路由不写 SQL（验收项：搜索 main.py 与路由不能出现 SQL）。

每个 HTTP 请求的边界：

1. FastAPI 依赖 `get_db()` 创建新 Session（`app/core/database.py`）；
2. 请求处理中所有写入在**同一个 Session** 内；
3. 请求结束 `finally: db.close()` 释放连接。

回滚的验证方式：`tests/test_day18_persistence.py::test_rollback_on_error` —— 插入一条外键不存在的 `EvaluationJob`，`flush()` 触发 `IntegrityError`，`rollback()` 后断言库里无残留记录，证明**部分写入被整体回滚**。

## 3. 未来如何换成 PostgreSQL

SQLAlchemy 2.x 的抽象让切换代价很小，但有几个真实差异点要处理：

1. **连接串**：`app/core/database.py` 里的 `create_engine(f"sqlite:///{DB_PATH}")` 换成 `create_engine("postgresql+psycopg://user:pass@host:5432/dbname")`，并增加 `psycopg`（或 `asyncpg`）依赖。URL 应来自配置对象（`app/core/config.py` 的 Settings），不能写死在代码里。
2. **JSON 列**：`evaluation_jobs.providers/evaluators` 用的 `JSON` 类型在 PostgreSQL 可映射为 `JSONB`（支持索引与查询），模型可保持 `Mapped[list]` 不变。
3. **外键约束**：PostgreSQL 默认开启外键，届时可移除 `tests/conftest.py` 里的 `PRAGMA foreign_keys=ON` 事件监听。
4. **分页**：`list_runs` 的 `offset/limit` 语法两个库通用，无需改动。
5. **并发**：PostgreSQL 支持并发写，`database is locked` 问题自然消失；但生产部署仍需连接池（SQLAlchemy 的 `pool_size` 配置）。

切换前建议先在本地跑通 Docker 版 PostgreSQL（Day 20 之后具备容器能力），并保留一个"SQLite 兼容模式"配置项，方便测试与演示继续用内存库。

## 当前 Schema 一览

- `datasets`：`id`(PK)、`name`(unique)
- `evaluation_jobs`：`id`(PK)、`dataset_id`(FK→datasets)、`status`、`providers`(JSON)、`evaluators`(JSON)、`concurrency`
- `evaluation_runs`：`id`(PK)、`job_id`(FK→evaluation_jobs)、`sample_index`、`status`、`score`

`EvaluationJob` 与 `EvaluationRun` 为一对多，`cascade="all, delete-orphan"`：删任务时其运行记录一并删除。
