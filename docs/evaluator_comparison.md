# Evaluator 对比与 EvalHub 最小协议（Day 25）

## 三仓库对比

| 仓库 | 输入协议 | 输出结构 | 风格 |
|---|---|---|---|
| DeepEval | measure(actual_output=..., expected_output=..., context=...) | metric.score / metric.success / metric.reason | 类对象 |
| OpenEvals | 函数参数（question/answer/expected_output...） | {score, comment} | 函数式 |
| OpenAI Evals | 声明式 yaml（class/key/data/eval） | 由注册 eval class 决定 | 配置驱动 |

## EvalHub 最小协议

- `BaseEvaluator.evaluate(item: EvaluationItem) -> EvaluationItem`
- 打分写进 `item.scores`；失败时 `item.passed=False` 并写 `item.reason`
- 优点：与 Day 22 工厂思想一致，新增评分器只注册一行

## 结论

三仓库协议各不相同；EvalHub 选"就地打分"是为了让聚合（metrics.py）和报告（Day 26）只读 EvaluationItem。