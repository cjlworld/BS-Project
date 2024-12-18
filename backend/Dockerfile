# 使用 Python 3.10-slim 作为基础镜像
FROM python:3.10-slim AS base

# 设置工作目录
WORKDIR /app

# debian12 的换源配置
RUN echo "Types: deb\n\
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian\n\
Suites: bookworm bookworm-updates bookworm-backports\n\
Components: main contrib non-free non-free-firmware\n\
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\
\n\
Types: deb\n\
URIs: https://security.debian.org/debian-security\n\
Suites: bookworm-security\n\
Components: main contrib non-free non-free-firmware\n\
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" > /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git

# 复制项目代码
COPY . .

# 安装 PDM
RUN pip install pdm -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装项目依赖
RUN pdm config pypi.url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pdm install --prod --no-self

# 安装 Playwright
# ENV PLAYWRIGHT_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/playwright PLAYWRIGHT_DOWNLOAD_TIMEOUT=120000
RUN pdm run playwright install --with-deps

# 裁剪
RUN rm -rf /var/lib/apt/lists/*

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["pdm", "run", "fastapi", "run"]