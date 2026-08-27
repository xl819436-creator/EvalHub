# EvalHub 评测数据集 Schema（v1.0）

## 字段表

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | str | 是 | 样本唯一标识 |
| `category` | str | 是 | 分类（math/knowledge/logic...） |
| `input` | str | 是 | 发送给模型的输入 |
| `expected` | str | 是 | 标准答案 |
| `evaluator_names` | list[str] | 否 | 该样本使用的评分器，默认 [] |
| `metadata` | dict | 否 | 附加信息，默认 {} |

## 哈希规则

- 规范化：`json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`
- 数据集哈希：所有记录规范化后按行拼接，再 SHA-256
- 为什么键排序：同内容不同键顺序应视为同一份数据，哈希必须一致

## 版本号

- `SCHEMA_VERSION = "1.0"`；字段变更时升版本号，旧数据不静默兼容

## 样例数据说明

- `examples/sample_dataset.jsonl`：6 条通用知识问答，无隐私、可公开