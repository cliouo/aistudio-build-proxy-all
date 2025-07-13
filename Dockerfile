# --- Stage 1: Go Builder ---
# 使用官方的 Go 镜像作为构建环境
FROM golang:1.22-alpine AS builder-go

# 声明代理构建参数，以便在构建时从外部传入
ARG http_proxy
ARG https_proxy
ARG no_proxy

# 设置环境变量，使其对该阶段内的所有 RUN 命令生效
# 这将影响下面的 'apk add' 命令
ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}
ENV no_proxy=${no_proxy}

# 安装 git 
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache git

# 设置工作目录
WORKDIR /src

# Go有自己的代理系统GOPROXY，这里设置为direct，会绕过我们设置的http_proxy
# 这通常是期望的行为，以确保直接从源码仓库拉取Go模块
ENV GOPROXY=direct
ENV GOSUMDB=off

# 复制 Go 项目的模块文件并下载依赖
COPY golang/go.mod ./
RUN go mod download

# 复制 Go 项目的源代码
COPY golang/ .

# 编译 Go 应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go_app_binary .


# --- Stage 2: Final Image ---
# 使用你原来的 Python 基础镜像
FROM python:3.11-slim

# 再次声明并设置代理参数，因为构建参数不会跨阶段继承
ARG http_proxy
ARG https_proxy
ARG no_proxy

ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}
ENV no_proxy=${no_proxy}

# 设置主工作目录
WORKDIR /app

# apt-get 现在会使用上面设置的代理来安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libxrender1 libxtst6 ca-certificates \
    fonts-liberation libasound2 libpangocairo-1.0-0 libpango-1.0-0 libu2f-udev xvfb \
    && rm -rf /var/lib/apt/lists/*

# 从 Go 构建阶段复制编译好的二进制文件到最终镜像中
COPY --from=builder-go /go_app_binary .

# 复制 Python 项目的 requirements.txt 并安装依赖
# pip 命令现在也会使用代理
COPY camoufox-py/requirements.txt ./camoufox-py/requirements.txt
RUN pip install --no-cache-dir -r ./camoufox-py/requirements.txt

# 运行 camoufox fetch
# 这个命令现在也会使用代理
RUN camoufox fetch

# 复制 Python 项目的所有文件
COPY camoufox-py/ .

# 复制 Supervisor 的配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# (可选，但推荐) 清理代理设置，避免在最终运行的容器中残留代理信息
# 除非你的应用在运行时也需要代理
ENV http_proxy="127.0.0.1:7890"
ENV https_proxy="127.0.0.1:7890"
ENV no_proxy="127.0.0.1:7890"

# 容器启动时，运行 Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
