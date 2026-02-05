FROM python:3.10-slim

WORKDIR /app

# 设置环境变量，防止 Python 生成 pyc 文件和缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（如果需要）
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 设置 Python 路径，确保能找到 src 模块
ENV PYTHONPATH=/app

# 运行应用
CMD ["python", "src/main.py"]
