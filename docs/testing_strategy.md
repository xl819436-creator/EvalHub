# EvalHub 测试策略

## 测试目标

测试重点是行为、错误边界和可复现性，不追求只覆盖代码行数。外部模型 API 和公网服务不进入默认测试套件。

## 分层策略

| 层 | 测试方式 | 典型内容 |
|---|---|---|
| 纯函数 | 参数化测试和异常断言 | 文本评分、成本、数据集哈希、重试分类 |
| Provider | MockProvider、MockTransport | success、timeout、429、invalid JSON、重试耗尽 |
| 数据访问 | 内存 SQLite、Fixture | 外键、事务回滚、分页、状态转换 |
| FastAPI | Starlette TestClient | 请求校验、统一错误、任务查询、取消、报告 |
| 集成演示 | 明确的本地命令 | Worker、Docker 健康检查、真实调用脚本 |

## 共享 Fixture

`tests/conftest.py` 提供内存 SQLite、每个测试重建表、外键约束和 FastAPI 数据库依赖覆盖。这样测试不会读取本机 `data/evalhub.db`，也不会依赖测试执行顺序。

同一个 Fixture 还会拦截出站公网连接，只放行本机回环地址。误调用收费 API 时测试应直接失败，而不是产生费用。

## 常用命令

在仓库根目录、已安装 `requirements.txt` 的 Python 3.11 环境中执行：

```powershell
python -m pytest -q
python -m pytest tests/test_day19_cost.py tests/test_day19_evaluator_parametrized.py tests/test_day19_loader_tmpdir.py tests/test_day19_provider_mock.py -q
python -m pytest tests/test_day21_deepseek_mapping.py tests/test_day21_real_call.py tests/test_day22_provider_factory.py tests/test_day23_retry.py -q
python -m pytest tests/test_day24_dataset_version.py tests/test_day26_api.py tests/test_day26_pipeline.py tests/test_day26_cancel.py -q
```

## 通过标准

- 测试不要求真实 API Key，不发送收费请求。
- 失败信息能指出样本、字段、状态码或错误类型。
- 参数化测试覆盖正常值、空值、边界值和非法值。
- 测试可以单独运行，不能依赖前一个测试留下的数据库或环境变量。
- README 只记录当前环境实际运行过的测试数量和性能数据。

## 真实调用与 Docker

真实 DeepSeek 调用是人工触发的演示，不属于默认 Pytest 流程；需要先检查 `.env`、预算和官方价格。Docker 验收单独检查镜像启动、`/health`、数据卷持久化和镜像不包含密钥。
