# EvalHub

EvalHub 是一个可复现的大语言模型自动化评测平台。本仓库从40天学习路线
的Day 10开始独立维护；每日学习过程保留在
[40day-lab](https://github.com/xl819436-creator/40day-lab)。

## 目录

- [Quick Start（快速开始）](#quick-start快速开始)
- [当前状态](#当前状态)
- [当前能力](#当前能力)
- [环境要求](#环境要求)
- [运行](#运行)
- [项目结构](#项目结构)
- [数据格式](#数据格式)
- [数据库设计](#数据库设计)
- [参考项目与自主实现边界](#参考项目与自主实现边界)
- [当前实现边界与限制](#当前实现边界与限制)
- [Day 1–10 阶段复盘](#day-110阶段复盘)
- [Day 11：Git/GitHub 可复现协作](#day-11gitgithub可复现协作)
- [Day 12：HTTP、REST 与接口调试](#day-12httprest与接口调试)
- [Day 13：async/await 与异常隔离](#day-13asyncawait与异常隔离)
- [安全](#安全)
- [Day 15：FastAPI API](#day-15fastapi-api)
- [容器化快速启动（Docker）](#容器化快速启动docker)
- [Day 19–26：EvalHub MVP 核心能力](#day-1926evalhub-mvp-核心能力)
- [当前 API 实际支持范围](#当前-api-实际支持范围)
- [从空目录复现](#从空目录复现)
- [开发进度与发布计划](#开发进度与发布计划)

## Quick Start（快速开始）

从空目录到跑通评测的最短路径：

```powershell
git clone https://github.com/xl819436-creator/EvalHub.git
cd EvalHub
conda create -n evalhub-py311 python=3.11 -y
conda activate evalhub-py311
python -m pip install -r requirements.txt
python -m pip check
python -m evalhub_core.health
python -m pytest -q
```

启动 API（Docker 方式，需要 Docker Desktop 正在运行）：

```powershell
docker compose up --build -d
# 浏览器打开 http://localhost:8000/docs
```

完整复现 SOP 见[从空目录复现](#从空目录复现)，接口清单见[当前 API 实际支持范围](#当前-api-实际支持范围)。

## 当前状态

- `origin/main` 代码基线已推进到 Day 26；本地工作树已进一步补齐 FastAPI 生命周期接口、Day 21 真实调用脚本和配套文档。
- 下一阶段是 Day 27：完成 v0.1.0 发布验收、基准实验和空目录复现。
- 当前版本为 `0.1.0-dev`，仓库目前没有 `v0.1.0` Release 或 tag。
- 本 README 描述的是当前工作树；提交到远程前，GitHub 上的 README 和代码仍是上一版。个人学习 Day 是否完成，仍以学习记录和验收结果为准。

## 当前能力

- 读取并验证UTF-8 JSONL评测数据集
- 输出文件名、行号和缺失字段等可执行错误提示
- 使用Exact Match生成单条结果和汇总报告
- 使用`BaseProvider`隔离业务逻辑与模型厂商
- 使用`MockProvider`模拟success、timeout、429和invalid JSON
- 使用Pydantic校验请求、响应、测试样本和Token用量
- 使用SQLite保存datasets、evaluation jobs和evaluation runs
- 为三张SQLite表提供完整CRUD、外键和事务保护
- 使用健康检查命令验证健康检查入口
- 使用HTTPX探测接口，并区分HTTP、超时和网络错误
- 使用asyncio比较等待型任务的串行与并发耗时
- 使用gather和TaskGroup并发执行任务并隔离单任务异常
- 使用httpx.AsyncClient并发请求并复用客户端连接池
- 使用Queue、Worker、Semaphore和超时控制执行20个异步任务
- 使用`BaseLLMProvider`、`DeepSeekProvider`、`MockLLMProvider`和`ProviderFactory`
- 对429/5xx/超时执行有上限的重试，并记录错误类型、状态码和重试次数
- 对数据集执行Pydantic校验、规范化SHA-256哈希和运行参数快照
- 提供Exact Match、JSON Schema评分器，以及成功率、准确率、格式率、P50/P95、Token和成本聚合
- 生成包含配置快照、分组指标、失败案例和已知限制的Markdown报告
- 提供FastAPI接口：数据集创建、评测任务创建/查询/取消和 Markdown 报告

## 环境要求

- Python 3.11或更高版本
- Conda
- Git

创建独立环境：

```powershell
conda create -n evalhub-py311 python=3.11 -y
conda activate evalhub-py311
python -m pip install -r requirements.txt
python -m pip check
```

## 运行

运行全部测试：

```powershell
python -m pytest -q
```

如果出现 `No module named pytest` 或其他依赖缺失，请确认当前终端已经激活本项目环境，并重新执行上面的依赖安装命令；不要使用另一个 Python 解释器运行测试。

查看命令行帮助：

```powershell
python -m evalhub_core --help
```

运行交互式Exact Match评测：

```powershell
python -m evalhub_core data/eval_dataset.jsonl
```

初始化本地SQLite数据库：

```powershell
python -m evalhub_core.database
```

数据库文件属于本地运行产物，已由`.gitignore`忽略。

运行健康检查：

```powershell
python -m evalhub_core.health
```

校验带 Schema 和哈希的数据集：

```powershell
python scripts/validate_dataset.py examples/sample_dataset.jsonl
```

运行 Day 14 的20任务 Worker 演示：

```powershell
python -m scripts.run_day14
```

探测HTTP接口：

```powershell
python scripts/http_probe.py https://httpbin.org/get 10
```

输出包含请求方法、URL、状态码、耗时和结果分类。退出码`0`表示成功，
`1`表示HTTP错误，`2`表示超时，`3`表示其他网络错误。

运行串行与异步并发实验：

```powershell
python -m scripts.async_runner
```

运行忘记`await`的警告实验：

```powershell
python -W always -m scripts.async_runner --forget-await
```

## 项目结构

```text
EvalHub/
├── data/
│   └── eval_dataset.jsonl
├── app/
│   ├── api/                 # FastAPI 路由和依赖
│   ├── core/                # 配置、数据库、中间件、错误处理
│   ├── models/              # SQLAlchemy 模型
│   ├── repositories/        # 数据访问
│   ├── schemas/             # 请求/响应模型
│   └── services/            # API 业务逻辑
├── docs/
│   ├── architecture.md
│   ├── database_decisions.md
│   ├── dataset_schema.md
│   ├── evaluator_comparison.md
│   ├── module_responsibilities.md
│   ├── provider_response_mapping.md
│   ├── retry_policy.md
│   ├── conflict_notes.md
│   ├── reproduce_sop.md
│   ├── testing_strategy.md
│   └── roadmap.md
├── evalhub_core/
│   ├── __init__.py
│   ├── __main__.py
│   ├── async_deepseek.py
│   ├── cli.py
│   ├── cost.py
│   ├── database.py
│   ├── dataset_version.py
│   ├── deepseek.py
│   ├── eval_runner.py
│   ├── evaluator.py
│   ├── evaluators.py
│   ├── health.py
│   ├── job_state_machine.py
│   ├── loader.py
│   ├── llm_config.py
│   ├── llm_provider.py
│   ├── metrics.py
│   ├── provider.py
│   ├── report_builder.py
│   ├── retry_policy.py
│   ├── schemas.py
│   ├── service.py
│   └── worker_pool.py
├── examples/
│   ├── eval_report.md
│   └── sample_dataset.jsonl
├── experiments/
│   └── async_vs_serial.md
├── notes/
│   ├── day24.md
│   ├── day25.md
│   ├── day26.md
│   └── httpx_reading_card.md
├── scripts/
│   ├── async_runner.py
│   ├── day21_real_call.py
│   ├── http_probe.py
│   ├── run_day14.py
│   └── validate_dataset.py
├── tests/                   # 离线行为测试和 API 测试
├── .env.example
├── .gitignore
├── LICENSE
├── pytest.ini
├── README.md
└── requirements.txt
```

## 数据格式

JSONL文件一行保存一条JSON对象：

```json
{"id":"case-001","input":"1 + 1 等于多少？","expected":"2","category":"math"}
```

必要字段：`id`、`input`、`expected`、`category`。

## 数据库设计

Day 10已实现：

- `datasets`
- `evaluation_jobs`
- `evaluation_runs`

三张表都具备Create、Read、Update、Delete。Provider暂时以
`provider_name`保存；后续创建`providers`表时再迁移为外键。

详细设计见[docs/architecture.md](docs/architecture.md)。

## 参考项目与自主实现边界

参考资料：

- [OpenAI Evals](https://github.com/openai/evals)：评测项目定位和结构
- [Pydantic](https://github.com/pydantic/pydantic)：数据模型与字段校验
- [Python.gitignore](https://github.com/github/gitignore/blob/main/Python.gitignore)：安全忽略规则

本仓库的JSONL加载器、评分器、Provider抽象、Pydantic模型和SQLite
CRUD均为学习者独立实现。本项目不是OpenAI Evals的Fork。

## 当前实现边界与限制

截至 Day 26，核心评测链路已经包含 Provider、评分器、SQLite、任务执行、取消和报告生成。
但这些能力还没有全部接入 FastAPI：当前 Web API 只创建数据集和评测任务，Day 26 的执行器、取消管理器和报告构建器仍主要通过 `evalhub_core` 模块和测试使用。

当前不包含：

- 前端页面
- 模型训练或微调
- 分布式任务系统
- 复杂权限系统
- Kubernetes
- FastAPI 的任务状态查询、取消和报告下载接口
- v0.1.0 正式 Release 和基准实验结果

## Day 1–10阶段复盘

以下结论以当前仓库中可运行的代码和测试为依据。

已掌握并完成实战：

- 使用函数、类、类型注解和Pydantic组织并校验评测数据
- 加载UTF-8 JSONL，定位错误行，并执行Exact Match评测
- 使用Provider接口隔离模型调用，使用Mock覆盖成功和失败路径
- 使用SQLite建表、处理主外键与事务，并完成三张表CRUD
- 使用Git分支、README、测试和公开仓库保存可复现产物

当前代码已覆盖真实 LLM 调用、重试、FastAPI 分层、异步 Worker、SQLAlchemy Repository、Docker 和数据集可复现性；后续仍需完成 Web API 的完整任务链路、v0.1.0 发布验收和空目录复现。

Day 11–20主要风险：

- 异步任务的异常如果没有隔离，可能导致整批评测中断
- Pydantic Schema、API字段和数据库列可能发生不一致
- SQLite并发写入可能产生锁竞争，事务边界需要明确
- Docker内外路径、环境变量和数据卷配置可能导致复现失败

## Day 11：Git/GitHub可复现协作

Day 11的目标是完整走通`feature branch → PR → review → merge`，并让其他人
能够按文档复现项目。

已完成：

- 用`feature/health-check`开发并合并最小健康检查
- 编写仓库无关的[Python项目复现SOP](docs/reproduce_sop.md)
- 在两个练习分支中制造并解决README冲突
- 保存[Git冲突练习记录](docs/conflict_notes.md)，说明选择最终内容的依据

验收命令：

```powershell
python -m evalhub_core.health
python -m pytest -q
git status
git log --oneline --graph --decorate -10
```

预期结果：健康检查正常、全部测试通过、工作区干净，并能在提交图中看到
功能分支和合并记录。

## Day 12：HTTP、REST与接口调试

Day 12的目标是读懂一次HTTP请求的来回数据，并把不同失败情况准确分类，
为后续接入真实模型API做准备。

已实现：

- 使用HTTPX发送带显式超时的同步GET请求
- 输出请求方法、URL、状态码和耗时，不输出Authorization等敏感信息
- 分类`200`、`400`、`401`、`404`、`429`、`500`、超时和网络错误
- 用测试替代不稳定的公网响应，稳定覆盖全部分类分支
- 编写[HTTPX QuickStart阅读卡](notes/httpx_reading_card.md)

运行探测脚本：

```powershell
python scripts/http_probe.py https://httpbin.org/get 10
```

运行Day 12测试：

```powershell
python -m pytest tests/test_http_probe.py -q
```

预期结果：脚本输出`result=<分类>`；测试覆盖成功、客户端错误、认证错误、
限流、服务端错误、超时和网络错误。公网接口的实际状态可能变化，因此验收
以自动化测试为准。

## Day 13：async/await与异常隔离

Day 13的目标是使用`asyncio`并发执行等待型任务，比较串行与并发耗时，
并保证单个任务失败时不会丢失其他任务结果。

已实现：

- 使用`asyncio.sleep()`模拟10个等待型模型请求
- 记录每个任务的开始时间、结束时间和实际耗时
- 使用串行方式依次执行任务
- 使用`asyncio.create_task()`和`asyncio.gather()`并发执行任务
- 使用Python 3.11的`asyncio.TaskGroup`管理并发任务
- 通过`run_safely()`将单任务异常转换成结构化错误结果
- 验证一个任务失败时仍然保留其他9个任务结果
- 使用`httpx.AsyncClient`执行异步HTTP请求
- 在整批HTTP请求中复用同一个客户端
- 使用`httpx.MockTransport`模拟HTTP响应，不依赖真实公网
- 保存[串行与并发实测报告](experiments/async_vs_serial.md)

运行串行与并发实验：

```powershell
python -m scripts.async_runner
```

程序依次运行：

1. 串行实验；
2. gather并发实验；
3. TaskGroup并发实验；
4. gather异常隔离实验；
5. TaskGroup异常隔离实验。

正常结果应满足：

```text
serial: success=10 error=0
gather: success=10 error=0
task_group: success=10 error=0
gather_with_error: success=9 error=1
task_group_with_error: success=9 error=1
```

具体耗时会受到操作系统调度和本机环境影响，以
[串行与并发实测报告](experiments/async_vs_serial.md)中的真实结果为准。

运行忘记`await`的警告实验：

```powershell
python -W always -m scripts.async_runner --forget-await
```

预期出现：

```text
RuntimeWarning: coroutine 'simulated_request' was never awaited
```

该警告表示协程对象已经创建，但没有使用`await`、
`asyncio.create_task()`或`asyncio.gather()`交给事件循环执行。

运行Day 13专项测试：

```powershell
python -m pytest tests/test_async_runner.py -q
```

测试覆盖：

- 串行执行返回10个成功结果
- gather和TaskGroup隔离单任务异常
- 每个结果包含计时信息
- 整批请求复用同一个AsyncClient
- HTTP成功、服务端错误、超时和网络错误分类
- 测试不发送真实公网请求

Day 13的并发属于等待型任务的异步并发，不是CPU多进程或GPU并行。

## 安全

`.env.example`只保存变量名。真实`.env`、API Key、PyCharm配置、
虚拟环境、数据库和生成输出均不得提交。

## Day 15：FastAPI API

启动（在仓库根目录执行）：

    python -m uvicorn app.main:app --reload

Swagger 文档：http://127.0.0.1:8000/docs

curl 示例（Windows PowerShell 中执行；`ds-1` 换成你创建数据集后返回的 id）：

    curl.exe -X POST http://127.0.0.1:8000/datasets -H "Content-Type: application/json" -d "{\"name\":\"demo\",\"samples\":[{\"input\":\"你好\",\"expected_output\":\"你好呀\"}]}"

    curl.exe -X POST http://127.0.0.1:8000/evaluations -H "Content-Type: application/json" -d "{\"dataset_id\":\"ds-1\",\"providers\":[\"mock\"],\"evaluators\":[\"exact_match\"],\"concurrency\":3}"

## 容器化快速启动（Docker）

前置：安装 Docker Desktop（Windows）并确保 Docker 引擎运行。

```powershell
# 1. 构建镜像并后台启动
docker compose up --build -d

# 2. 查看健康状态（等待 healthy）
docker compose ps

# 3. 打开交互式 API 文档
# 浏览器访问 http://localhost:8000/docs

# 4. 停止容器（数据卷保留，数据不丢）
docker compose down

# 5. 再次启动，数据仍在
docker compose up -d
```

健康检查：

```powershell
Invoke-RestMethod http://localhost:8000/health
```

预期返回：

```json
{"status":"ok","service":"evalhub"}
```

`docker compose down` 不会删除命名数据卷；如果执行 `docker compose down -v`，会同时删除 SQLite 数据卷，请只在确认不需要数据时使用。

## Day 19–26：EvalHub MVP 核心能力

仓库 `main` 已合并以下阶段的主要代码；本地工作树补齐了本次缺失的脚本、文档和 API，具体验收仍以对应测试和实测日志为准：

| Day | 已实现内容 | 主要交付物 |
|---:|---|---|
| 19 | Pytest Fixture、参数化、Mock、禁止真实公网测试 | `tests/test_day19_*.py`、`docs/testing_strategy.md` |
| 20 | Dockerfile、Compose、SQLite 数据卷和健康检查 | `Dockerfile`、`compose.yaml`、`.dockerignore` |
| 21 | DeepSeek 响应映射、真实调用脚本、结构化 JSON 错误边界、成本计算 | `evalhub_core/deepseek.py`、`scripts/day21_real_call.py`、`docs/provider_response_mapping.md` |
| 22 | BaseLLMProvider、DeepSeek/Mock Provider、Factory | `evalhub_core/llm_provider.py`、`llm_config.py` |
| 23 | 429/5xx/超时重试、Retry-After、错误分类 | `evalhub_core/retry_policy.py`、`async_deepseek.py` |
| 24 | 数据集 Schema、SHA-256、版本和运行参数快照 | `evalhub_core/dataset_version.py`、`scripts/validate_dataset.py` |
| 25 | Exact Match、JSON Schema、聚合指标和分组 | `evalhub_core/evaluators.py`、`metrics.py` |
| 26 | 任务状态机、局部失败、取消幂等和 Markdown 报告 | `evalhub_core/eval_runner.py`、`job_state_machine.py`、`report_builder.py` |

对应的离线测试命令：

```powershell
python -m pytest tests/test_day19_cost.py tests/test_day19_evaluator_parametrized.py tests/test_day19_loader_tmpdir.py tests/test_day19_provider_mock.py -q
python -m pytest tests/test_day21_deepseek_mapping.py tests/test_day22_provider_factory.py tests/test_day23_retry.py -q
python -m pytest tests/test_day24_dataset_version.py tests/test_metrics.py tests/test_day26_pipeline.py tests/test_day26_cancel.py -q
```

Day 21 的真实调用需要本地 `.env` 和可用 API 余额，会产生费用。先复制 `.env.example` 为 `.env` 并填写密钥，再人工运行：

```powershell
Copy-Item .env.example .env
python scripts/day21_real_call.py
```

默认测试不调用真实模型；真实调用脚本会检查单日预算、保存脱敏响应样例并记录 Token/成本。

## 当前 API 实际支持范围

当前 FastAPI 应用实际暴露的接口如下：

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/` | 返回服务信息 |
| GET | `/health` | 返回健康状态 |
| POST | `/datasets` | 创建数据集 |
| POST | `/evaluations` | 创建待执行的评测任务 |
| GET | `/evaluations/{job_id}` | 查询任务状态和 run 摘要，可分页 |
| POST | `/evaluations/{job_id}/cancel` | 持久化取消任务，重复请求幂等 |
| GET | `/evaluations/{job_id}/report` | 返回当前已持久化结果的 Markdown 报告 |

当前 `POST /evaluations` 负责创建 `pending` 任务，查询、取消和报告接口已经接入 FastAPI；自动启动后台 Worker、实时执行模型调用和把每条输入/期望答案完整写入 API 数据库仍是后续工作。

## 从空目录复现

以下流程只依赖公开仓库，不引用原电脑的绝对路径：

```powershell
git clone https://github.com/xl819436-creator/EvalHub.git
cd EvalHub
conda create -n evalhub-py311 python=3.11 -y
conda activate evalhub-py311
python -m pip install -r requirements.txt
python -m pip check
python -m evalhub_core.health
python scripts/validate_dataset.py examples/sample_dataset.jsonl
python -m pytest -q
```

Windows Docker 复现还需要 Docker Desktop 正在运行：

```powershell
docker compose up --build -d
Invoke-RestMethod http://localhost:8000/health
docker compose ps
docker compose down
```

复现时应记录 Python 版本、依赖安装结果、Git commit SHA、测试结果和遇到的报错；不要提交 `.env`、API Key、数据库、虚拟环境或 IDE 配置。

## 开发进度与发布计划

- 当前 `origin/main` 的代码基线：Day 26 报告功能合并后的提交 `69d383e`。
- 本地工作树已补齐 Day 21 真实调用脚本、Provider 映射文档、测试策略文档和 FastAPI 任务生命周期接口，尚未 commit/push。
- 下一步：Day 27，完成至少 30 个测试、基准实验、空目录复现和 `v0.1.0` Release。
- 最近一次本地验证：Python 3.11.15、pytest 8.4.2，`184 passed`；真实模型调用未执行。
