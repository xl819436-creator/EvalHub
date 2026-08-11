# Day 11 Git 冲突练习记录

## 冲突场景

从同一个 `main` 提交创建了两个分支：

- `practice/conflict-a`
- `practice/conflict-b`

两个分支都修改了 README 第一行，因此 Git 无法自动合并。

## 分支 A 的修改

```text
# EvalHub A：可复现评测工具
```

分支 A 提交：

```text
362aae5
```

## 分支 B 的修改

```text
# EvalHub B：LLM 评测平台
```

分支 B 提交：

```text
845ff25
```

## Git 冲突内容

```text
<<<<<<< HEAD
# EvalHub B：LLM 评测平台
=======
# EvalHub A：可复现评测工具
>>>>>>> practice/conflict-a
```

## 最终保留内容

```text
# EvalHub
```

冲突解决提交：

```text
0571284
```

## 保留原因

本次修改只用于练习 Git 冲突，不应该借练习改变正式项目名称。

分支 A 和分支 B 的新标题都没有经过正式讨论，因此最终恢复原来的项目名称 `EvalHub`。

## 解决步骤

```powershell
git merge practice/conflict-a
git status
git diff
git add README.md
git commit -m "merge: resolve controlled README conflict"
```

## 验证命令

```powershell
git diff --name-only --diff-filter=U
Get-Content .\README.md -TotalCount 1
python -m evalhub_core.health
python -m pytest -q
git status
git log --oneline --graph --decorate --all -15
```

## 学习结论

Git 可以识别两个版本无法自动合并，但不能替开发者决定最终业务内容。

解决冲突后必须：

1. 删除冲突标记。
2. 检查最终内容。
3. 暂存解决结果。
4. 提交解决结果。
5. 重新运行测试。