"""Day 26：Markdown 报告生成（配置快照 / 分组指标 / 失败案例 / 已知限制）。"""

from evalhub_core.dataset_version import build_run_manifest


def build_markdown_report(job_id: str, manifest: dict | None = None, groups: dict | None = None,
                          failures: list[dict] | None = None) -> str:
    manifest = manifest or build_run_manifest([])
    groups = groups or {}
    failures = failures or []
    lines = [
        f"# EvalHub 评测报告：{job_id}",
        "",
        "## 配置快照",
        f"- dataset_hash: `{manifest.get('dataset_hash', '')}`",
        f"- git_commit: `{manifest.get('git_commit', '')}`",
        f"- provider: {manifest.get('provider', '')}",
        f"- model: {manifest.get('model', '')}",
        f"- seed: {manifest.get('seed', '')}",
        f"- start_time: {manifest.get('start_time', '')}",
        "",
        "## 榜单（分组指标）",
        "| category | total | success_rate | accuracy |",
        "|---|---|---|---|",
    ]
    for category, agg in groups.items():
        lines.append(f"| {category} | {agg['total']} | {agg['success_rate']:.2%} | {agg['accuracy']:.2f} |")
    lines.append("")
    lines.append("## 失败案例")
    if failures:
        for f in failures:
            lines.append(f"- **{f['id']}**：expected=`{f['expected']}`, actual=`{f['actual']}`, reason={f['reason']}")
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 已知限制")
    lines.append("- 本报告数字来源于 EvaluationRun 表，可逐条追溯（report -> run -> input）。")
    lines.append("- 成本为估算值，以 DeepSeek 官方定价页为准。")
    return "\n".join(lines)