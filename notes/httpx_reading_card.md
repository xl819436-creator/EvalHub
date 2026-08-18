# HTTPX QuickStart 阅读卡

## 1. 同步请求入口

```python
response = httpx.get(url, timeout=10.0)
```

同步请求会等待当前请求完成，再执行下一行代码。

## 2. 异步请求入口

```python
async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=10.0)
```

异步请求使用 `AsyncClient` 和 `await`。

Day 12 只要求找到并看懂这个入口；Day 13 再正式实现异步请求。

## 3. timeout

HTTPX 官方默认的网络不活动超时是5秒。

本项目显式使用：

```python
timeout=10.0
```

显式设置的好处是代码审查时能直接看到最长等待时间。

## 4. HTTP状态错误与网络错误

### HTTPStatusError

服务器已经返回响应，但状态码不是2xx。

必须先调用：

```python
response.raise_for_status()
```

4xx或5xx才会变成 `HTTPStatusError`。

### RequestError

请求过程中出现连接、DNS、代理、协议或其他网络问题。

### TimeoutException

`TimeoutException` 是 `RequestError` 的子类，表示连接、读取、写入或连接池等待超时。

## 5. Day 12错误映射

| 情况 | 项目分类 | 处理原则 |
|---|---|---|
| 200–299 | OK | 正常读取响应 |
| 400、404等 | ClientError | 检查参数、URL或资源 |
| 401 | AuthError | 检查身份信息，不盲目重试 |
| 429 | RateLimitError | 可能等待后重试 |
| 500–599 | ServerError | 记录服务端错误 |
| HTTPX超时 | TimeoutError | 停止等待并记录 |
| 其他网络错误 | NetworkError | 检查网络、地址和代理 |

429的自动重试策略留到 Day 23，今天只做准确分类。

## 6. 一次真实公网请求与响应摘要

```text
method=GET
url=https://httpbin.org/get
status=503
elapsed=4.782s
result=ServerError
json=无
Authorization=未发送