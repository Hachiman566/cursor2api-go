# 故障排除指南

## 403 Access Denied 错误

### 问题描述
在使用一段时间后,服务突然开始返回 `403 Access Denied` 错误:
```
ERRO[0131] Cursor API returned non-OK status             status_code=403
ERRO[0131] Failed to create chat completion              error="{\"error\":\"Access denied\"}"
```

### 原因分析
1. **Token 过期**: `x-is-human` token 缓存时间过长,导致 token 失效
2. **频率限制**: 短时间内发送过多请求触发了 Cursor API 的速率限制
3. **重复 Token**: 使用相同的 token 进行多次请求被识别为异常行为

### 解决方案

#### 1. 已实施的自动修复
最新版本已经包含以下改进:

- **动态浏览器指纹**: 每次请求使用真实且随机的浏览器指纹信息
  - 根据操作系统自动选择合适的平台配置 (Windows/macOS/Linux)
  - 随机 Chrome 版本 (120-130)
  - 随机语言设置和 Referer
  - 真实的 User-Agent 和 sec-ch-ua headers
- **缩短缓存时间**: 将 `x-is-human` token 缓存时间从 30 分钟缩短到 1 分钟
- **自动重试机制**: 遇到 403 错误时自动清除缓存并重试(最多 2 次)
- **指纹刷新**: 403 错误时自动刷新浏览器指纹配置
- **错误恢复**: 失败时自动清除缓存,确保下次请求使用新 token
- **指数退避**: 重试时使用递增的等待时间

#### 2. 手动解决步骤
如果问题持续存在:

1. **重启服务**:
   ```bash
   # 停止当前服务 (Ctrl+C)
   # 重新启动
   ./cursor2api-go
   ```

2. **检查日志**:
   查看是否有以下日志:
   - `Received 403 Access Denied, clearing token cache and retrying...` - 自动重试
   - `Failed to fetch x-is-human token` - Token 获取失败
   - `Fetched x-is-human token` - Token 获取成功

3. **等待冷却期**:
   如果频繁遇到 403 错误,建议等待 5-10 分钟后再使用

4. **检查网络**:
   确保能够访问 `https://cursor.com`

#### 3. 预防措施

1. **控制请求频率**: 避免在短时间内发送大量请求
2. **监控日志**: 注意 `x-is-human token` 的获取频率
3. **合理配置超时**: 在 `.env` 文件中设置合理的超时时间

### 配置建议

在 `.env` 文件中:
```bash
TIMEOUT=120  # 增加超时时间,避免频繁重试
MAX_INPUT_LENGTH=100000  # 限制输入长度,减少请求大小
```

### 调试模式

如果需要查看详细的调试信息,可以启用调试模式:
```bash
# 方式 1: 修改 .env 文件
DEBUG=true

# 方式 2: 使用环境变量
DEBUG=true ./cursor2api-go
```

这将显示:
- 每次请求的 `x-is-human` token (前 50 字符)
- 请求的 payload 大小
- 重试次数
- 详细的错误信息

## Docker 部署常见问题

### 问题 1：apk 无法连接到 Alpine 包仓库

**现象**:
```
WARNING: fetching https://dl-cdn.alpinelinux.org/alpine/v3.23/main/aarch64/APKINDEX.tar.gz: Connection refused
ERROR: unable to select packages: git (no such package)
```

**原因**: Docker 构建环境无法访问 Alpine CDN（网络限制或代理问题）。

**解决方案**: 已在 Dockerfile 中修复：
- 构建阶段改用 `golang:1.24`（Debian 基础镜像），内置 git 和 ca-certificates，无需 `apk` 安装
- 运行阶段改用 `node:20-slim`（Debian，内置 Node.js），无需任何 `apk` 命令

---

### 问题 2：go mod download 失败，提示 proxyconnect 连接拒绝

**现象**:
```
go: github.com/andybalholm/brotli@v1.2.0: Get "https://proxy.golang.org/...":
proxyconnect tcp: dial tcp 127.0.0.1:7890: connect: connection refused
```

**原因**: 宿主机设置了 HTTP 代理（如 Clash、V2Ray 等监听在 `127.0.0.1:7890`），Docker BuildKit 会自动将宿主机的 `HTTP_PROXY`/`HTTPS_PROXY` 注入到构建过程中，容器内无法访问宿主机的本地代理。

**解决方案**: 在 Dockerfile 的 `RUN` 命令中内联清除代理，并设置国内 Go 模块代理：
```dockerfile
ENV GOPROXY=https://goproxy.cn,https://proxy.golang.org,direct

RUN HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" go mod download
RUN HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o cursor2api-go .
```

> **注意**: 在 Dockerfile 中用 `ENV HTTP_PROXY=""` 无效，BuildKit 预定义的代理参数优先级更高，必须在 `RUN` 命令内联覆盖。

---

### 问题 3：容器内访问 cursor.com 失败 (SSL EOF / TLS 握手错误)

**现象**:
```
error="Post \"https://cursor.com/api/chat\": EOF"
# 或
SSL connection using TLSv1.3 / UNDEF
```

**原因**: Alpine Linux 使用 musl libc 和较老的 OpenSSL，与 `req` 库的 TLS 指纹模拟 (`ImpersonateChrome()`) 不兼容。

**解决方案**: 使用 Debian 基础镜像（已在当前 Dockerfile 中修复）：
```dockerfile
# 改用 node:20-slim (Debian)
FROM node:20-slim

RUN apt-get update && apt-get install -y ca-certificates
```

> 注：切换到 Debian 后容器可直接访问 cursor.com，无需代理。

---

## 其他常见问题

### Cloudflare 403 错误
如果看到 `Cloudflare 403` 错误,说明请求被 Cloudflare 防火墙拦截。这通常是因为:
- IP 被标记为可疑
- User-Agent 不匹配
- 缺少必要的浏览器指纹

**解决方案**: 检查 `.env` 文件中的浏览器指纹配置（`USER_AGENT`、`UNMASKED_VENDOR_WEBGL`、`UNMASKED_RENDERER_WEBGL`）是否正确。

### 连接超时
如果频繁出现连接超时:
1. 检查网络连接
2. 增加 `.env` 文件中的 `TIMEOUT` 配置值
3. 检查防火墙设置

### Token 获取失败
如果无法获取 `x-is-human` token:
1. 检查 `.env` 文件中的 `SCRIPT_URL` 配置是否正确
2. 确保 `jscode/main.js` 和 `jscode/env.js` 文件存在
3. 检查 Node.js 环境是否正常安装（Node.js 18+）

## 联系支持

如果问题仍未解决,请提供以下信息:
1. 完整的错误日志
2. `.env` 文件配置（隐藏敏感信息如 `API_KEY`）
3. 使用的 Go 版本和 Node.js 版本
4. 操作系统信息
