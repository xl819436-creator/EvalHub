
# Day 14 学习笔记：Queue、Worker、Semaphore 与超时

日期：2026-08-21 ｜ 视频：BV16kTazbEwe P10-P13（超时）、BV1KvzVB5EhU（Queue）、BV1GoJJzyEan（Semaphore）

## 1. 生产者/消费者模式

- `asyncio.Queue` 在生产者和消费者之间解耦：生产者只管 put，消费者只管 get，互不知道对方节奏。
- 评测场景：外部不断提交评测任务（生产者），固定数量的 Worker 随到随取（消费者）。这是 EvalHub 的执行骨架。
- 与 Day 13 的区别：Day 13 的 gather 是"一次性把已知任务并发跑完"；Day 14 的队列是"任务可以持续进来，Worker 池长期运行"。

## 2. Semaphore 信号量

- `asyncio.Semaphore(3)` 是计数器：进入 `async with semaphore:` 时计数 -1，退出时 +1；计数为 0 时后续协程排队等待。
- 作用：不管有多少 Worker，同时在跑的 handler 最多 3 个。
- Worker 数 vs Semaphore：Worker 数限制"消费者数量"，Semaphore 限制"正在执行的任务数"，两者都限制并发但作用点不同。
- 统计写法：active_count 的增减必须都在临界区内部，否则统计超过真实并发。

## 3. 超时与取消

- `asyncio.wait_for(coro, timeout)`：超时后取消内部协程并抛 TimeoutError。
- 捕获后生成结构化结果：status=TIMEOUT, error_type="TimeoutError" —— 超时也是一种结果。
- Python 3.11 新语法 `asyncio.timeout(seconds)` 上下文管理器可对比学习。
- 关键：wait_for 只包单个任务的 handler，超时只影响该任务，不拖住整个池。

## 4. task_done() / join() 协议（最容易踩的坑）

- `queue.join()` 等待"put 次数 == task_done() 次数"才返回。
- 因此每个 get() 必须配对一次 task_done()，包括 sentinel！漏一次 join() 就永远不返回。
- 实战 3 已演示：get 后不调 task_done -> wait_for(q.join(), 0.2) 超时；补上后立即返回。

## 5. sentinel 优雅停止

- 给每个 Worker 的队尾放哨兵对象（SENTINEL = object()），Worker 取到它就知道"没活了"，处理完手头任务后 return。
- 为什么不用 task.cancel()：硬取消会留下未完成任务，产生 "Task was destroyed but it is pending" 警告。
- sentinel 数量必须 == Worker 数量（每个 Worker 各收一个）。

## 6. 与 Day 13 对比

| 维度 | Day 13 async_runner | Day 14 worker_pool |
|---|---|---|
| 并发方式 | gather / TaskGroup 一次性 | Queue + 固定 Worker 池持续消费 |
| 任务来源 | 预先构造的列表 | 可动态入队 |
| 并发上限 | 由任务数决定 | Semaphore 显式限制 |
| 超时 | 无（单任务异常隔离） | wait_for 结构化超时 |
| 停止 | 全部 await 完自然结束 | sentinel 优雅停止 |

## 7. 一句话复述

评测引擎 = 生产者把任务放进队列 + 固定 Worker 排队消费 + Semaphore 压住并发 + 超时兜底 + 哨兵收尾。