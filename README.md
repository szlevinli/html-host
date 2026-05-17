# html-host

私有 HTML 文件托管服务，部署于 `coffeedou.cc`。

## 本地开发

```bash
uv sync
uv run uvicorn html_host.main:app --reload  # API: http://localhost:8000
open frontend/index.html                    # 前端
```

运行测试：

```bash
uv run pytest
uv run ruff check .
uv run basedpyright
```

## 环境变量

参考 `.env.example`，本地开发复制为 `.env` 填写：

| 变量 | 说明 |
|------|------|
| `ADMIN_PASSWORD` | 登录密码 |
| `JWT_SECRET` | JWT 签名密钥，随机长字符串 |
| `JWT_EXPIRE_DAYS` | Token 有效天数，默认 7 |
| `BASE_URL` | 服务访问地址，用于拼接文件 URL |
| `UPLOAD_DIR` | 上传文件存储目录 |
| `DB_PATH` | SQLite 数据库路径 |
| `MAX_FILE_SIZE_MB` | 上传文件大小限制，默认 2 |

## VPS 部署信息

- **服务器**：阿里云 ECS，SSH 别名 `aliyun`
- **域名**：`coffeedou.cc`
- **系统用户**：`web`（nologin，专用于运行服务进程）

### 目录结构

| 路径 | 用途 | Owner |
|------|------|-------|
| `/opt/html-host` | 代码仓库 + `.venv` | root |
| `/opt/html-host/.env` | 生产环境变量（不进 git） | root |
| `/var/www/html-host` | 上传的 HTML 文件，nginx 直接 serve | web |
| `/var/lib/html-host` | SQLite 数据库 | web |

### nginx

配置片段见 `deploy/nginx/html-host.conf`，需追加到 `/etc/nginx/conf.d/coffeedou.cc.conf` 的 443 server block 中。

### systemd

service 文件见 `deploy/systemd/html-host.service`，安装到 `/etc/systemd/system/`。

### 首次部署（一次性手动操作）

```bash
# 1. clone 代码
git clone <repo-url> /opt/html-host

# 2. 安装依赖
/root/.local/bin/uv sync --no-dev --project /opt/html-host

# 3. 创建生产 .env
cp /opt/html-host/.env.example /opt/html-host/.env
# 编辑 .env 填写 ADMIN_PASSWORD、JWT_SECRET

# 4. 安装 systemd service
cp /opt/html-host/deploy/systemd/html-host.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now html-host

# 5. 更新 nginx 配置
# 将 deploy/nginx/html-host.conf 的内容追加到
# /etc/nginx/conf.d/coffeedou.cc.conf 的 443 server block 中
nginx -t && systemctl reload nginx
```

### 日常部署

push 到 `main` 分支后，GitHub Actions 自动完成 CI 测试和 CD 部署。
