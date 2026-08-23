# 模块职责（Day 17 目录映射）

| 目录 | 一句话职责 | 禁止做什么 |
|---|---|---|
| app/api | 定义路由，转发请求 | 禁止写业务逻辑 / SQL |
| app/services | 业务规则与状态转换 | 禁止直接操作数据库 |
| app/repositories | 数据存取 | 禁止包含业务规则 |
| app/schemas | 请求/响应模型与校验 | 禁止访问数据库 |
| app/core | 配置、中间件、错误契约 | 禁止依赖具体业务 |
| app/models | ORM 模型（Day 18） | 禁止写业务逻辑 |
| evalhub_core | 领域能力（加载/评分/Provider） | 禁止被 API 直接调用（经 service） |