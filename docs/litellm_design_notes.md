# LiteLLM 设计借鉴与 Provider 类图（Day 22）

## LiteLLM 借鉴了什么、不照搬什么

对照 <https://github.com/BerriAI/litellm> README 与 provider/router 目录名，记录 5 条"借鉴 / 不照搬"：

1. **借鉴**：统一接口思想——业务方只面对一个 `generate(request) -> response`，不关心背后是哪家厂商。
   **不照搬**：LiteLLM 接几百家厂商，我们用工厂 + 注册表只维护自己需要的 Provider（DeepSeek / Mock / Dummy）。
2. **借鉴**：配置驱动切换——用配置选 Provider，而不是改代码。
   **不照搬**：不引入 LiteLLM 的 Router/重试中间件体系，重试策略（Day 23）自己用 httpx + 策略类实现，可控可测。
3. **借鉴**：密钥只从环境变量读取，配置里只放"环境变量名"。
   **不照搬**：不复制 LiteLLM 的 key 管理/代理计费逻辑。
4. **借鉴**：错误分类——把厂商错误映射成统一错误类型，业务层不感知具体厂商。
   **不照搬**：不照抄 LiteLLM 的异常树，我们沿用 Day 21 的 `ErrorType`（timeout/rate_limit/invalid_json/provider_error）。
5. **借鉴**：Provider 目录按厂商划分、可插拔注册。
   **不照搬**：不照搬其动态加载机制，用简单的 `ProviderFactory.register()` 注册表（实战题 1 演示新增 DummyProvider 零改动业务层）。

## Provider 依赖图（API → Service → Provider interface → 具体 Provider）

```mermaid
flowchart LR
    API[FastAPI 路由] --> SVC[EvaluationService]
    SVC --> IFACE[BaseLLMProvider 接口<br/>generate(request) -> LLMResponse]
    IFACE --> DS[DeepSeekProvider<br/>真实调用 httpx]
    IFACE --> MOCK[MockLLMProvider<br/>success/timeout/429/invalid_json]
    IFACE --> DUM[DummyProvider<br/>实战题演示]
    FACTORY[ProviderFactory<br/>注册表 + LLMConfig] --> IFACE
    CONFIG[LLMConfig<br/>provider/model/base_url/timeout<br/>api_key_env] --> FACTORY
    DS --> MAPPING[map_deepseek_response<br/>Day 21 厂商映射]
```

文字版（不依赖 mermaid 渲染时也能看）：
`FastAPI 路由 → EvaluationService → BaseLLMProvider（统一接口）→ 具体 Provider（DeepSeek/Mock/Dummy），由 ProviderFactory 按 LLMConfig 创建；业务层不 import 任何厂商 SDK，也不出现 if provider == 某厂商。`

## 关键文件

- `evalhub_core/llm_config.py`：LLMConfig（pydantic，配置驱动）
- `evalhub_core/llm_provider.py`：BaseLLMProvider / DeepSeekProvider / MockLLMProvider / DummyProvider / ProviderFactory
- `tests/test_day22_provider_factory.py`：9 个用例（含未知 provider 报错、DummyProvider 注册）
