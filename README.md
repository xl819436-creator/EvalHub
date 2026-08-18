# EvalHub

EvalHub 是一个可复现的大语言模型自动化评测平台。本仓库从 40 天学习路线
的 Day 10 开始独立维护；每日学习过程保留在
[40day-lab](https://github.com/xl819436-creator/40day-lab)。

## 当前能力

- 读取并验证 UTF-8 JSONL 评测数据集
- 输出文件名、行号和缺失字段等可执行错误提示
- 使用 Exact Match 生成单条结果和汇总报告
- 使用 `BaseProvider` 隔离业务逻辑与模型厂商
- 使用 `MockProvider` 模拟 success、timeout、429 和 invalid JSON
- 使用 Pydantic 校验请求、响应、测试样本和 Token 用量
- 使用 SQLite 保存 datasets、evaluation jobs 和 evaluation runs
- 为三张 SQLite 表提供完整 CRUD、外键和事务保护
- 使用健康检查命令验证项目入口和本地数据库
- 使用 HTTPX 探测接口，并区分 HTTP、超时和网络错误

## 环境要求

- Python 3.10
- Conda
- Git

创建独立环境：

```powershell
conda create -n evalhub-py310 python=3.10 -y
conda activate evalhub-py310
python -m pip install -r requirements.txt
python -m pip check
```

## 运行

运行全部测试：

```powershell
python -m pytest -q
```

查看命令行帮助：

```powershell
python -m evalhub_core --help
```

运行交互式 Exact Match 评测：

```powershell
python -m evalhub_core data/eval_dataset.jsonl
```

初始化本地 SQLite 数据库：

```powershell
python -m evalhub_core.database
```

数据库文件属于本地运行产物，已由 `.gitignore` 忽略。

运行健康检查：

```powershell
python -m evalhub_core.health
```

探测 HTTP 接口：

```powershell
python scripts/http_probe.py https://httpbin.org/get 10
```

输出包含请求方法、URL、状态码、耗时和结果分类。退出码 `0` 表示成功，
`1` 表示 HTTP 错误，`2` 表示超时，`3` 表示其他网络错误。

## 项目结构

```text
EvalHub/
├── data/
│   └── eval_dataset.jsonl
├── docs/
│   ├── architecture.md
│   ├── conflict_notes.md
│   ├── reproduce_sop.md
│   └── roadmap.md
├── evalhub_core/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── database.py
│   ├── evaluator.py
│   ├── loader.py
│   ├── provider.py
│   ├── schemas.py
│   └── service.py
├── notes/
│   └── httpx_reading_card.md
├── scripts/
│   └── http_probe.py
├── tests/
├── .env.example
├── .gitignore
├── LICENSE
├── pytest.ini
├── README.md
└── requirements.txt
```

## 数据格式

JSONL 文件一行保存一条 JSON 对象：

```json
{"id":"case-001","input":"1 + 1 等于多少？","expected":"2","category":"math"}
```

必要字段：`id`、`input`、`expected`、`category`。

## 数据库设计

Day 10 已实现：

- `datasets`
- `evaluation_jobs`
- `evaluation_runs`

三张表都具备 Create、Read、Update、Delete。Provider 暂时以
`provider_name` 保存；后续创建 `providers` 表时再迁移为外键。

详细设计见 [docs/architecture.md](docs/architecture.md)。

## 参考项目与自主实现边界

参考资料：

- [OpenAI Evals](https://github.com/openai/evals)：评测项目定位和结构
- [Pydantic](https://github.com/pydantic/pydantic)：数据模型与字段校验
- [Python.gitignore](https://github.com/github/gitignore/blob/main/Python.gitignore)：安全忽略规则

本仓库的 JSONL 加载器、评分器、Provider 抽象、Pydantic 模型和 SQLite
CRUD 均为学习者独立实现。本项目不是 OpenAI Evals 的 Fork。

## MVP 边界

v0.1.0 计划包含 Provider、评分器、SQLite、FastAPI、后台任务和报告。

暂不包含：

- 前端页面
- 模型训练或微调
- 分布式任务系统
- 复杂权限系统
- Kubernetes

## Day 1–10 阶段复盘

以下结论以当前仓库中可运行的代码和测试为依据。

已掌握并完成实战：

- 使用函数、类、类型注解和 Pydantic 组织并校验评测数据
- 加载 UTF-8 JSONL，定位错误行，并执行 Exact Match 评测
- 使用 Provider 接口隔离模型调用，使用 Mock 覆盖成功和失败路径
- 使用 SQLite 建表、处理主外键与事务，并完成三张表 CRUD
- 使用 Git 分支、README、测试和公开仓库保存可复现产物

仍需在后续学习日掌握：

- 真实 LLM API 的超时、限流、重试和成本控制
- FastAPI 分层、异步队列、后台 Worker 与统一错误响应
- SQLAlchemy Repository、并发写入和数据库迁移
- Docker 运行、持久化配置和全新机器复现

Day 11–20 主要风险：

- 异步任务的异常如果没有隔离，可能导致整批评测中断
- Pydantic Schema、API 字段和数据库列可能发生不一致
- SQLite 并发写入可能产生锁竞争，事务边界需要明确
- Docker 内外路径、环境变量和数据卷配置可能导致复现失败

## Day 11：Git/GitHub 可复现协作

Day 11 的目标是完整走通 `feature branch → PR → review → merge`，并让其他人
能够按文档复现项目。

已完成：

- 用 `feature/health-check` 开发并合并最小健康检查
- 编写仓库无关的 [Python 项目复现 SOP](docs/reproduce_sop.md)
- 在两个练习分支中制造并解决 README 冲突
- 保存 [Git 冲突练习记录](docs/conflict_notes.md)，说明选择最终内容的依据

验收命令：

```powershell
python -m evalhub_core.health
python -m pytest -q
git status
git log --oneline --graph --decorate -10
```

预期结果：健康检查正常、全部测试通过、工作区干净，并能在提交图中看到
功能分支和合并记录。

## Day 12：HTTP、REST 与接口调试

Day 12 的目标是读懂一次 HTTP 请求的来回数据，并把不同失败情况准确分类，
为后续接入真实模型 API 做准备。

已实现：

- 使用 HTTPX 发送带显式超时的同步 GET 请求
- 输出请求方法、URL、状态码和耗时，不输出 Authorization 等敏感信息
- 分类 `200`、`400`、`401`、`404`、`429`、`500`、超时和网络错误
- 用测试替代不稳定的公网响应，稳定覆盖全部分类分支
- 编写 [HTTPX QuickStart 阅读卡](notes/httpx_reading_card.md)

运行探测脚本：

```powershell
python scripts/http_probe.py https://httpbin.org/get 10
```

运行 Day 12 测试：

```powershell
python -m pytest tests/test_http_probe.py -q
```

预期结果：脚本输出 `result=<分类>`；测试覆盖成功、客户端错误、认证错误、
限流、服务端错误、超时和网络错误。公网接口的实际状态可能变化，因此验收
以自动化测试为准。

## 安全

`.env.example` 只保存变量名。真实 `.env`、API Key、PyCharm 配置、
虚拟环境、数据库和生成输出均不得提交。
