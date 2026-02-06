FROM python:3.12-slim

# 1. 设置环境变量
# 确保 Python 打印日志不被缓存，方便调试
ENV PYTHONUNBUFFERED=1
# 显式指定工作目录和数据目录 (适配你的 Python 代码逻辑)
ENV APP_WORK_DIR=/app/data

WORKDIR /app

# 2. [关键修复] 更换 Debian 镜像源 (解决 apt update 超时/失败问题)
# 这里使用阿里云镜像源，替换原本的 deb.debian.org
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 3. 安装系统依赖
# 合并 update 和 install 减少层数，清理缓存减小体积
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. 安装 Python 依赖
COPY requirements.txt .
# 使用国内 pip 源加速下载
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 复制代码
COPY . .

# 6. 创建数据目录并赋予权限
# 这里的 /app/data 将用来存放 database.db 和 assets
RUN mkdir -p /app/data/assets /app/logs

# 7. 声明数据卷 (只挂载目录，不挂载单个文件)
VOLUME ["/app/data", "/app/logs"]

# Expose port
EXPOSE 11451

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "11451"]