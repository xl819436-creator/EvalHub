# 基础镜像：Python 3.11 精简版（无编译工具，镜像更小）
FROM python:3.11-slim

# 固定工作目录，后续所有命令都在这里执行
WORKDIR /app

# 先复制依赖清单并安装：利用 Docker 层缓存，requirements 不变时不重装
# 使用清华镜像源：files.pythonhosted.org 在国内经常超时
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60

# 再复制项目代码（.dockerignore 已排除测试、密钥、缓存）
COPY app ./app
COPY evalhub_core ./evalhub_core

# 数据库目录（数据卷挂载点）
RUN mkdir -p /app/data

# 暴露容器内端口 8000
EXPOSE 8000

# 启动 Uvicorn：监听 0.0.0.0 才能被宿主机访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]