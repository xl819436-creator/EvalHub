# EvalHub

EvalHub 是一个可复现的大语言模型自动化评测平台。本仓库从40天学习路线
的Day 10开始独立维护；每日学习过程保留在
[40day-lab](https://github.com/xl819436-creator/40day-lab)。

## 当前能力

- 读取并验证UTF-8 JSONL评测数据集
- 输出文件名、行号和缺失字段等可执行错误提示
- 使用Exact Match生成单条结果和汇总报告
- 使用`BaseProvider`隔离业务逻辑与模型厂商
- 使用`MockProvider`模拟success、timeout、429和invalid JSON
- 使用Pydantic校验请求、响应、测试样本和Token用量
- 使用SQLite保存datasets、evaluation jobs和evaluation runs
- 为三张SQLite表提供完整CRUD、外键和事务保护
- 使用健康检查命令验证项目入口和本地数据库
- 使用HTTPX探测接口，并区分HTTP、超时和网络错误
- 使用asyncio比较等待型任务的串行与并发耗时
- 使用gather和TaskGroup并发执行任务并隔离单任务异常
- 使用httpx.AsyncClient并发请求并复用客户端连接池

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
│   ├── health.py
│   ├── loader.py
│   ├── provider.py
│   ├── schemas.py
│   └── service.py
├── experiments/
│   └── async_vs_serial.md
├── notes/
│   └── httpx_reading_card.md
├── scripts/
│   ├── async_runner.py
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

## MVP边界

v0.1.0计划包含Provider、评分器、SQLite、FastAPI、后台任务和报告。

暂不包含：

- 前端页面
- 模型训练或微调
- 分布式任务系统
- 复杂权限系统
- Kubernetes

## Day 1–10阶段复盘

以下结论以当前仓库中可运行的代码和测试为依据。

已掌握并完成实战：

- 使用函数、类、类型注解和Pydantic组织并校验评测数据
- 加载UTF-8 JSONL，定位错误行，并执行Exact Match评测
- 使用Provider接口隔离模型调用，使用Mock覆盖成功和失败路径
- 使用SQLite建表、处理主外键与事务，并完成三张表CRUD
- 使用Git分支、README、测试和公开仓库保存可复现产物

仍需在后续学习日掌握：

- 真实LLM API的超时、限流、重试和成本控制
- FastAPI分层、异步队列、后台Worker与统一错误响应
- SQLAlchemy Repository、并发写入和数据库迁移
- Docker运行、持久化配置和全新机器复现

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