# Day 13：串行与异步并发实验

## 1. 实验目标

本实验比较10个等待型任务在以下三种执行方式下的总耗时：

1. 串行执行；
2. `asyncio.create_task()` 与 `asyncio.gather()` 并发执行；
3. `asyncio.TaskGroup` 并发执行。

实验同时验证以下行为：

- 一个任务抛出异常时，其他任务的结果是否仍能保留；
- 忘记使用 `await` 时，Python会产生什么警告；
- 多个异步HTTP请求是否复用同一个 `httpx.AsyncClient`；
- 为什么本实验属于异步并发，而不是GPU并行。

## 2. 实验环境

- 实验日期：2026-08-18
- 操作系统：Windows
- Python版本：`<<PYTHON_VERSION>>`
- Python解释器：`D:\Annaconda\envs\evalhub-py311\python.exe`
- httpx版本：`<<HTTPX_VERSION>>`
- pytest版本：`<<PYTEST_VERSION>>`
- Python是否支持TaskGroup：是
- 实验样本数：10

模拟任务的等待时间为：

```text
0.2、0.3、0.4、0.5、0.6、0.7、0.8、0.9、1.0、0.2秒
```

全部等待时间之和为5.6秒，最长单任务等待时间为1.0秒。

5.6秒和1.0秒只用于解释理论预期；最终结论使用的是本机实际运行结果。

## 3. 实验代码

实验入口：

```text
scripts/async_runner.py
```

专项测试：

```text
tests/test_async_runner.py
```

运行目录：

```text
D:\PycharmProjects\EvalHub-course
```

正常实验命令：

```powershell
D:\Annaconda\envs\evalhub-py311\python.exe -m scripts.async_runner
```

这里使用模块运行方式：

```text
-m scripts.async_runner
```

不能直接运行：

```text
scripts\async_runner.py
```

原因是脚本内部使用了包式导入：

```python
from scripts.http_probe import classify_status
```

使用 `-m` 从项目根目录运行时，Python能够正确找到 `scripts` 命名空间包和其中的 `http_probe.py`。

## 4. 串行与并发实测结果

| 实验 | 总耗时/秒 | 成功数 | 错误数 |
|---|---:|---:|---:|
| 串行执行 | <<SERIAL_SECONDS>> | 10 | 0 |
| gather并发 | <<GATHER_SECONDS>> | 10 | 0 |
| TaskGroup并发 | <<TASK_GROUP_SECONDS>> | 10 | 0 |
| gather异常隔离 | <<GATHER_ERROR_SECONDS>> | 9 | 1 |
| TaskGroup异常隔离 | <<TASK_GROUP_ERROR_SECONDS>> | 9 | 1 |

本次实验的原始汇总输出为：

```text
serial: total=<<SERIAL_SECONDS>>s success=10 error=0
gather: total=<<GATHER_SECONDS>>s success=10 error=0
task_group: total=<<TASK_GROUP_SECONDS>>s success=10 error=0
gather_with_error: total=<<GATHER_ERROR_SECONDS>>s success=9 error=1
task_group_with_error: total=<<TASK_GROUP_ERROR_SECONDS>>s success=9 error=1
```

## 5. 加速比

计算公式：

```text
加速比 = 串行总耗时 ÷ 并发总耗时
```

本次实测结果：

- gather相对于串行的加速比：`<<GATHER_SPEEDUP>>` 倍；
- TaskGroup相对于串行的加速比：`<<TASK_GROUP_SPEEDUP>>` 倍。

根据实测数据，gather和TaskGroup的总耗时都明显低于串行执行。

## 6. 为什么并发快于串行

串行执行时，程序会等待当前任务完成，再启动下一个任务。

执行顺序类似：

```text
任务0等待并完成
→ 任务1等待并完成
→ 任务2等待并完成
→ 继续执行后面的任务
```

因此，串行总耗时接近所有任务等待时间之和。

并发执行时，程序会先创建多个任务。当其中一个任务正在等待
定时器或网络响应时，事件循环可以运行其他已经就绪的任务。

执行方式类似：

```text
启动任务0
启动任务1
启动任务2
启动其他任务
→ 事件循环在等待期间调度其他任务
```

因此，并发总耗时主要接近最慢任务的等待时间，而不是全部等待
时间之和。

本实验中的任务主要消耗时间在 `asyncio.sleep()`，它模拟了模型
API或其他HTTP接口的网络等待过程，因此适合使用异步并发。

## 7. 异常隔离实验

实验故意让：

```text
task_id=4
```

抛出：

```text
RuntimeError
```

实测结果：

- 返回结果总数：10；
- 成功结果数：9；
- 错误结果数：1；
- 其他任务结果是否丢失：否。

底层任务通过以下代码真实抛出异常：

```python
if should_fail:
    raise RuntimeError(
        f"task {task_id} failed intentionally"
    )
```

异步调用器通过 `run_safely()` 在单个任务边界捕获异常，并将异常
转换为结构化错误结果。

错误结果中包含：

```text
task_id
status
started_at
finished_at
elapsed
error_type
error
```

因此，一个任务失败时，其他9个任务仍然可以继续执行并保留结果。

## 8. gather与TaskGroup的区别

### asyncio.gather

本实验使用：

```python
await asyncio.gather(
    *tasks,
    return_exceptions=True,
)
```

`gather()` 用于等待一组任务完成。

设置：

```python
return_exceptions=True
```

后，未处理异常可以作为结果返回，而不是立即中断结果收集。

### asyncio.TaskGroup

`TaskGroup` 是Python 3.11提供的结构化并发工具。

它通过：

```python
async with asyncio.TaskGroup() as group:
```

管理一组任务的创建、等待和退出。

如果TaskGroup中的某个任务产生未处理异常，TaskGroup会取消同组
其他尚未完成的任务，并在退出时抛出异常组。

因此，本实验没有把预期的业务异常直接留给TaskGroup处理，而是
先通过 `run_safely()` 将异常转换为错误结果。

准确的职责划分是：

```text
TaskGroup负责管理任务生命周期；
run_safely负责隔离单任务异常。
```

## 9. 忘记await实验

实验命令：

```powershell
D:\Annaconda\envs\evalhub-py311\python.exe -W always -m scripts.async_runner --forget-await
```

本次观察到的真实警告为：

```text
<<MISSING_AWAIT_WARNING>>
```

产生警告的原因是：

```python
simulated_request(...)
```

只创建了一个协程对象，但没有使用以下任何一种方式执行它：

```python
await simulated_request(...)
```

```python
task = asyncio.create_task(
    simulated_request(...)
)
await task
```

```python
await asyncio.gather(
    simulated_request(...),
)
```

调用 `async def` 函数并不代表函数体已经真正执行。只有协程被
`await` 或被事件循环调度后，函数体才会运行。

因此，忘记 `await` 时，Python会发出：

```text
coroutine was never awaited
```

警告。

## 10. 为什么这不是GPU并行

本实验使用的是 `asyncio` 异步并发。

它主要解决的是等待型任务，例如：

- HTTP请求；
- 模型API调用；
- 定时器等待；
- 异步文件或网络I/O。

当一个任务等待时，事件循环可以运行其他协程，从而减少整批任务
的总等待时间。

它没有自动完成以下行为：

- 没有把Python代码分配到多个CPU核心；
- 没有调用CUDA；
- 没有将计算任务提交给GPU；
- 没有让多个CPU密集型函数真正同时计算。

因此，本实验属于等待型任务的异步并发，不是多线程计算、
多进程计算或GPU并行。

## 11. 为什么复用一个AsyncClient

Day 12的同步请求使用：

```python
httpx.get(url, timeout=timeout)
```

Day 13改为：

```python
async with httpx.AsyncClient(...) as client:
    response = await client.get(url)
```

`probe_many()` 只创建一次 `httpx.AsyncClient`，再将同一个客户端
传给全部 `async_probe()` 任务。

复用客户端的主要好处包括：

- 复用底层连接池；
- 减少重复建立TCP连接的开销；
- 减少重复关闭连接的开销；
- 统一管理超时配置；
- 在批量请求中获得更稳定的资源管理方式。

不推荐在每个 `async_probe()` 任务内部重新创建客户端，因为那会
让每个请求分别创建和关闭连接池，失去客户端复用的意义。

## 12. 为什么测试不访问真实公网

本实验使用：

```python
httpx.MockTransport
```

模拟HTTP响应。

测试覆盖：

- 200正常响应；
- 500服务端错误；
- HTTP读取超时；
- 网络连接失败；
- 多个请求复用同一个AsyncClient。

这样做可以避免以下外部因素影响测试：

- `httpbin.org` 临时不可用；
- 外部服务返回非预期503；
- 本机代理差异；
- DNS问题；
- 网络速度波动；
- 真实接口限流。

因此，自动测试验证的是代码逻辑，而不是外部网站当时是否正常。

## 13. 测试结果

Day 13专项测试命令：

```powershell
D:\Annaconda\envs\evalhub-py311\python.exe -m pytest tests\test_async_runner.py -q
```

专项测试结果：

```text
<<DAY13_TEST_RESULT>>
```

全量回归测试命令：

```powershell
D:\Annaconda\envs\evalhub-py311\python.exe -m pytest -q
```

全量回归结果：

```text
<<FULL_TEST_RESULT>>
```

专项测试用于验证Day 13新增功能，全量回归测试用于确认Day 13
没有破坏此前已经实现的功能。

## 14. 最终结论

本次实验验证了以下结论：

1. 对以等待为主的任务，异步并发总耗时明显低于串行执行；
2. `asyncio.gather` 和 `asyncio.TaskGroup` 都能并发运行10个任务；
3. 单个任务抛出异常后，其他9个任务结果仍然能够保留；
4. `TaskGroup` 本身不等于异常隔离，预期异常需要在任务边界处理；
5. 忘记 `await` 会导致协程没有真正执行，并产生
   `coroutine was never awaited` 警告；
6. 本实验利用的是等待时间，不是GPU并行；
7. 同一批HTTP请求应复用一个 `httpx.AsyncClient`；
8. 使用 `MockTransport` 可以让HTTP测试摆脱真实公网的不确定性。