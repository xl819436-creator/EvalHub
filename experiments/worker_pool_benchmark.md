# 实验报告：Worker 数量对总耗时与峰值并发的影响

日期：2026-08-21 ｜ 项目：EvalHub Day 14

## 环境

- 机器：（CPU/内存）
- Python：3.11.15（D:\Annaconda\envs\evalhub-py311）
- 依赖：asyncio（stdlib）、pytest 8.4.2
- 样本：20 个任务（17 正常 sleep 0.2-0.7s + 1 挂起触发超时 + 1 故意失败），Semaphore(3)，timeout=3.0s

## 命令

    python -m scripts.run_day14 --workers 1 --concurrency 3
    python -m scripts.run_day14 --workers 3 --concurrency 3
    python -m scripts.run_day14 --workers 10 --concurrency 3

## 实测数据

| workers | 总耗时(s) | max_active | 说明 |
|---|---:|---:|---|
| 1 |  |  | 单 worker 串行消费，最慢 |
| 3 |  |  | 3 个 worker 并行，明显提速 |
| 10 |  |  | 被 Semaphore(3) 压住，与 3 基本持平 |

## 结论

1. workers 1 -> 3：总耗时明显下降，3 个 worker 并行消费队列。
2. workers 3 -> 10：总耗时基本不变，并发上限被 Semaphore(3) 卡住，验证"并发瓶颈在信号量"。
3. max_active 三组应为 1、3、3，是并发上限生效的直接证据。
4. 若实测与预期不符：说明原因（如 sleep 太短导致调度噪声），不硬凑数字。

## 对 EvalHub 的意义

Day 26 后台任务将复用这个骨架：评测任务入队 -> 固定 Worker 消费 -> Semaphore 保护 Provider 限流 -> 超时兜底单个请求。