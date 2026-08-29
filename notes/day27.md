# Day 27：EvalHub v0.1.0 验收、基准实验与第一次发布

## 实战 2：并发提高后 P95 为什么不一定下降

并发提高后 P95 不一定下降，因为 P95 是尾延迟，并发高时排队和资源竞争可能让最慢的请求更慢。

## 1. 测试验收（30+ 测试）

- 全量测试：`python -m pytest -q`
- 结果：`184 passed in 4.56s`（远超 30+ 要求，2026-08-29 复现验证）
- 测试覆盖：加载器、评分器、Provider 抽象、Pydantic 模型、SQLite CRUD、HTTP 探测分类、异步并发与异常隔离、Worker 池、任务状态机、FastAPI 接口

## 2. 基准实验（1/5/10 并发）

- 报告：`docs/benchmark.md`
- 原始输出：`docs/benchmark_raw.txt`（`scripts/benchmark_concurrency.py` 直接输出，未修改）
- 方法：固定 50 条 Mock 数据，Exact Match，每条模拟 0.01s 等待
- 结果摘要：

| 并发度 | 吞吐（条/秒） | 平均延迟（ms） | P95（ms） | 失败率 |
|---:|---:|---:|---:|---:|
| 1 | 63.38 | 15.76 | 16.10 | 10% |
| 5 | 323.01 | 15.43 | 16.32 | 10% |
| 10 | 656.26 | 15.17 | 15.60 | 10% |

- 结论：吞吐量随并发近似线性提升；P95 不随并发单调下降（实测 5 并发时 P95 反而略高），印证实战 2 的答案。

## 3. 空目录复现记录（2026-08-29）

复现目录：`D:\tmp\evalhub-repro\EvalHub`（全新 clone，不引用原电脑任何路径）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 1. 克隆 | `git clone https://github.com/xl819436-creator/EvalHub.git` | ✅ HEAD `4970229` |
| 2. 安装依赖 | `python -m pip install -r requirements.txt` | ✅ |
| 3. 依赖检查 | `python -m pip check` | ✅ No broken requirements found |
| 4. 健康检查 | `python -m evalhub_core.health` | ✅ `{"status": "ok", "service": "evalhub"}` |
| 5. 全量测试 | `python -m pytest -q` | ✅ `184 passed in 4.56s` |
| 6. 启动 API | `python -m uvicorn app.main:app --port 8000` | ✅ 监听 127.0.0.1:8000 |
| 7. 健康接口 | `GET /health` | ✅ `{"status":"ok","service":"evalhub"}` |
| 8. 创建数据集 | `POST /datasets` | ✅ `{"dataset_id":"ds-1","name":"demo","sample_count":3}` |
| 9. 创建评测任务 | `POST /evaluations`（mock + exact_match，concurrency=3） | ✅ `{"job_id":"job-ds-1-1","status":"pending"}` |
| 10. 查询状态 | `GET /evaluations/job-ds-1-1` | ✅ 返回 job 详情与 run 摘要 |
| 11. 导出报告 | `GET /evaluations/job-ds-1-1/report` | ✅ 生成 Markdown 报告 |

说明：当前 API 的实际支持范围是"创建 pending 任务 + 查询 + 取消 + 报告"，后台 Worker 自动执行仍是后续工作，报告数字来自已持久化的 EvaluationRun 表。

## 4. 实战 3：对一个失败用例写最小可复现步骤

以基准实验中的失败用例为例（`expected="2"` 但 `actual="3"`，Exact Match 判定失败）：

```python
"""最小可复现：一条 Exact Match 失败用例。"""
from evalhub_core.evaluators import EvaluationItem, ExactMatchEvaluator

item = EvaluationItem(
    id="case-0",
    category="math",
    input="1+1等于几？",
    expected="2",
    actual="3",  # 模型输出与期望不一致
)

result = ExactMatchEvaluator().evaluate(item)

assert result.passed is False, "期望失败但通过了"
assert result.expected == "2"
assert result.actual == "3"
```

复现步骤：

1. 激活环境：`conda activate evalhub-py311`
2. 在仓库根目录保存上面的代码为 `reproduce_failure.py`
3. 运行：`python reproduce_failure.py`
4. 预期：`assert` 全部通过（即失败用例被正确识别为失败）；若任何断言失败，说明评分逻辑异常

## 5. 实战 1：同学按 README 复现的卡点记录模板

请同学（或新机器）在不提问的情况下按 README 从空目录复现，记录卡点：

| 卡点序号 | 卡在哪个步骤 | 同学的原话/表现 | 原因分析 | README 需要改进的点 |
|---|---|---|---|---|
| 1 | （示例）`conda activate` 找不到环境 | "evalhub-py311 不存在" | 同学没有先 `conda create` | 在 Quick Start 里补一条"先创建环境"的提示 |
| 2 | | | | |
| 3 | | | | |

## 6. Release 状态

- tag `v0.1.0`：已创建并推送（`git tag v0.1.0 && git push origin v0.1.0`）
- GitHub Release：网页发布待完成（正文包含 Features / Known limitations / Reproduce，参考 `docs/benchmark.md` 与 README 功能表）
- 建议提交信息：`release: evalhub v0.1.0`
