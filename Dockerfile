# 构建阶段
FROM golang:1.24 AS builder

# 设置工作目录
WORKDIR /app

# 清除宿主机代理，使用公共 Go 模块代理
ENV GOPROXY=https://goproxy.cn,https://proxy.golang.org,direct

# 复制go mod文件
COPY go.mod go.sum ./

# 下载依赖（清除代理环境变量，避免宿主机代理干扰）
RUN HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" go mod download

# 复制源码
COPY . .

# 构建应用
RUN HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o cursor2api-go .

# 运行阶段 - 使用 Debian 基础镜像获得更好的 TLS 支持
FROM node:20-slim

# 安装 ca-certificates（带重试机制）
RUN set -e; \
    HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 创建非 root 用户 (不指定特定 UID)
RUN useradd -m appuser

WORKDIR /home/appuser

# 从构建阶段复制二进制文件
COPY --from=builder /app/cursor2api-go .

# 复制静态文件和 JS 代码（需要用于 JavaScript 执行）
COPY --from=builder /app/static ./static
COPY --from=builder /app/jscode ./jscode

# 更改所有者
RUN chown -R appuser:appuser /home/appuser

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:8002/health || exit 1

# 启动应用
CMD ["./cursor2api-go"]