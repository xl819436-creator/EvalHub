P95 手算 95.5，与代码一致（2026-08-24 实测）
内容正确性与格式合法性是两个独立指标，必须分开评分

位置偏差：输出排在前面更容易得高分 → 缓解：随机交换顺序、多次采样；
自利偏差：Judge 偏爱与自身风格相似的回答 → 缓解：双盲、交换模型身份；
啰嗦/长度偏差：更长的回答常被高估 → 缓解：长度归一化或按要点打分；
一致性与校准偏差：Judge 评分不稳定/过于自信 → 缓解：多次采样取多数、与人工标注校准。

三仓库输入输出各不相同：DeepEval 用命名参数+对象、
OpenEvals 用函数+{score,comment}、OpenAI Evals 用 yaml 声明。
EvalHub 的最小协议定为 BaseEvaluator.evaluate(item: EvaluationItem) -> EvaluationItem（打分写进 item.scores）。 
理由：我们的评分器只需在 EvaluationItem 上读写分数，无需返回独立对象，且与 Day 22 工厂思想一致。