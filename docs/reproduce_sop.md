# 通用 Python 项目复现 SOP

## 目标

从陌生 Python 仓库开始，确认代码版本、创建隔离环境、安装依赖、准备配置和数据、找到最小入口，并记录可验证的输出。

## 1. 固定复现对象

记录：

- 仓库 URL
- commit SHA
- 操作系统
- Python 版本
- 复现日期

```powershell
git remote -v
git rev-parse HEAD
python --version
python -c "import sys; print(sys.executable)"
```

不要只记录分支名，因为分支指向的提交可能继续变化。

## 2. 先读再决定是否 clone

优先查看：

- README
- LICENSE
- 项目目录
- 依赖文件
- 最小示例
- 自动化测试
- 最近提交
- Issue
- Release

## 3. 识别 Python 版本

依次检查：

1. `.python-version`
2. `pyproject.toml`
3. `setup.py`
4. `setup.cfg`
5. `requirements.txt`
6. `Dockerfile`
7. GitHub Actions
8. README

如果不同文件的版本要求不一致，应记录为复现风险。

## 4. 创建隔离环境

```powershell
conda create -n project-env python=3.10 -y
conda activate project-env
python --version
python -c "import sys; print(sys.executable)"
```

不要向系统 Python 安装项目依赖。

## 5. 安装并检查依赖

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

安装失败时记录：

- 失败的包名
- Python 版本
- 操作系统
- 执行命令
- 完整错误信息

## 6. 准备配置

检查：

- `.env.example`
- 环境变量
- 配置文件示例
- 数据库设置
- 外部服务地址
- API Key 要求

不得提交：

- 真实 `.env`
- API Key
- 密码
- 访问令牌
- 本地数据库
- IDE 配置

## 7. 准备数据

确认：

- 数据来源
- 文件格式
- 必填字段
- 示例数据
- 相对路径
- 预处理步骤

## 8. 找到最小入口

常见入口：

```powershell
python main.py
python -m package_name
python -m pytest -q
```

优先运行不调用收费 API 的最小示例。

## 9. 记录实际输出

记录：

- 执行命令
- 退出码
- 标准输出
- 错误输出
- 测试数量
- 运行时间
- 是否访问网络
- 是否调用收费 API

不得虚构测试结果、准确率、延迟或运行时间。

## 10. 固定排错顺序

```text
版本 → 依赖 → 路径 → 配置 → 数据 → 入口 → 输出
```

每次只改变一个变量，然后重新执行相同的最小命令。

## 11. 判断复现结果

- 成功：按说明得到预期输出。
- 部分成功：核心模块运行，但外部依赖缺失。
- 失败：最小入口仍不能运行，并已保存错误证据。
- 无法判断：缺少必要文档、数据、配置或权限。

## 12. 复现记录模板

```markdown
- 仓库：
- commit SHA：
- 操作系统：
- Python 版本：
- 安装命令：
- 运行命令：
- 实际输出：
- 测试结果：
- 复现结论：
- 阻塞问题：
```