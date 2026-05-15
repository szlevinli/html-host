# html-host 工程化方案

## 项目定位

部署在 coffeedou.cc 的私有 HTML 文件托管服务。目标：小而专业，可迭代，可验证，可扩展。

---

## 工程原则

- **可迭代**：API 版本化，数据库变更通过迁移管理，前后端解耦
- **可验证**：完整测试覆盖（单元 + 集成），本地可完整运行，CI 门控
- **可扩展**：分层架构，业务逻辑与框架解耦，配置驱动

---

## 仓库结构

```
html-host/
├── backend/
│   ├── pyproject.toml           # 项目元数据、依赖、工具配置
│   ├── src/
│   │   └── html_host/
│   │       ├── __init__.py
│   │       ├── main.py          # FastAPI app 入口
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── __init__.py
│   │       │       ├── router.py    # 路由聚合
│   │       │       ├── files.py     # /files 端点
│   │       │       └── schemas.py   # Pydantic request/response
│   │       ├── core/
│   │       │   ├── config.py    # pydantic-settings 配置
│   │       │   └── security.py  # Token 验证逻辑
│   │       ├── db/
│   │       │   ├── base.py      # SQLAlchemy engine/session
│   │       │   ├── models.py    # ORM 模型
│   │       │   └── migrations/  # Alembic 迁移文件
│   │       └── services/
│   │           └── file_service.py  # 业务逻辑（与框架无关）
│   └── tests/
│       ├── conftest.py          # pytest fixtures
│       ├── test_files_api.py    # API 集成测试
│       └── test_file_service.py # 单元测试
├── frontend/
│   └── index.html               # 纯 HTML + JS 上传页面
├── deploy/
│   ├── nginx/
│   │   └── html-host.conf       # nginx location 片段
│   └── systemd/
│       └── html-host.service    # systemd unit 文件
├── Makefile                     # 常用命令入口
├── .env.example                 # 环境变量模板
├── .github/
│   └── workflows/
│       └── ci.yml               # CI 流水线
└── README.md
```

---

## 技术栈

| 层 | 技术 | 选型理由 |
|---|---|---|
| 运行时 | Python 3.12 | 稳定，类型支持好 |
| 包管理 | uv | 快，lockfile，替代 pip/poetry |
| Web 框架 | FastAPI | 原生异步，自动 OpenAPI 文档 |
| ORM | SQLAlchemy 2.x (async) | 即使用 SQLite 也走迁移管理 |
| 数据库迁移 | Alembic | schema 变更可追溯 |
| 配置管理 | pydantic-settings | 类型安全的 env var |
| Linter | ruff | 统一 lint + format |
| 类型检查 | basedpyright | 严格模式 |
| 测试 | pytest + pytest-asyncio + httpx | 异步测试支持 |
| 覆盖率 | pytest-cov | 门控最低覆盖率 |
| 前端 | 原生 HTML + JS | 无构建步骤，够用 |
| CSS | Pico.css CDN | 轻量美化 |
| 进程管理 | systemd | VPS 标准方案 |
| Web 服务 | nginx | 反代 + 静态托管 |

---

## pyproject.toml

```toml
[project]
name = "html-host"
version = "0.1.0"
description = "Private HTML file hosting service"
requires-python = ">=3.12"
dependencies = [
    # Web 框架
    "fastapi>=0.115",
    # ASGI 服务器
    "uvicorn[standard]>=0.30",
    # 文件上传支持（FastAPI UploadFile 依赖）
    "python-multipart>=0.0.9",
    # ORM
    "sqlalchemy[asyncio]>=2.0",
    # SQLite 异步驱动
    "aiosqlite>=0.20",
    # 数据库迁移
    "alembic>=1.13",
    # 配置管理
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = [
    # 测试
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",          # AsyncClient，用于集成测试
    "pytest-cov>=5.0",
    # 代码质量
    "ruff>=0.4",
    "basedpyright>=1.18",
    # 提交钩子
    "pre-commit>=3.7",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/html_host"]

# ── ruff ──────────────────────────────────────────────────
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade（自动提示旧式类型注解）
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
]

[tool.ruff.lint.isort]
known-first-party = ["html_host"]

# ── basedpyright ──────────────────────────────────────────
[tool.basedpyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
venvPath = "."
venv = ".venv"
reportMissingImports = true
reportAny = true

# ── pytest ────────────────────────────────────────────────
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=html_host --cov-report=term-missing"

[tool.coverage.run]
source = ["src/html_host"]
omit = ["src/html_host/db/migrations/*"]
```

---

## API 设计

Base path：`/html-upload-api/v1`（版本化，为未来 v2 留空间）

```
POST   /v1/auth/login     密码换 JWT（无需认证）
POST   /v1/files          上传文件
GET    /v1/files          获取文件列表
DELETE /v1/files/{code}   删除文件
GET    /health            健康检查（无需认证）
```

认证：JWT（HS256），通过 `POST /v1/auth/login` 用密码换取，有效期由 `JWT_EXPIRE_DAYS` 控制（默认 7 天）。所有 `/v1/files/*` 端点通过 FastAPI Dependency 注入统一验证 Bearer JWT。密码和 JWT 签名密钥均从环境变量读取（`ADMIN_PASSWORD`、`JWT_SECRET`）。

### 响应结构统一

```json
// 成功
{
  "data": { ... },
  "error": null
}

// 失败
{
  "data": null,
  "error": { "code": "UNAUTHORIZED", "message": "..." }
}
```

---

## 数据库

```sql
-- files 表
CREATE TABLE files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code  TEXT    NOT NULL UNIQUE,
    filename    TEXT    NOT NULL,          -- 原始文件名，展示用
    size_bytes  INTEGER NOT NULL,
    upload_time TEXT    NOT NULL           -- ISO 8601
);
```

通过 Alembic 管理，初始版本为 `0001_initial`，后续变更追加迁移文件，不手动修改表结构。

---

## 配置管理

`.env.example`：
```
UPLOAD_TOKEN=change-me
BASE_URL=https://coffeedou.cc
UPLOAD_DIR=/var/www/html-host
DB_PATH=/opt/html-host/data.db
MAX_FILE_SIZE_MB=2
```

pydantic-settings 在启动时验证所有字段，缺失或类型错误则拒绝启动，避免配置错误在运行时才暴露。

---

## 测试策略

| 层次 | 内容 | 工具 |
|---|---|---|
| 单元测试 | file_service 核心逻辑，short_code 生成唯一性 | pytest |
| 集成测试 | API 端点完整流程（上传→查询→删除），认证校验 | httpx AsyncClient + 临时 SQLite |
| 覆盖率门控 | 低于 80% CI 失败 | pytest-cov |

本地运行：
```bash
make test          # 跑所有测试
make test-cov      # 带覆盖率报告
```

---

## CI 流水线（GitHub Actions）

```
push / PR
    ↓
[lint]        ruff check + ruff format --check
    ↓
[typecheck]   basedpyright
    ↓
[test]        pytest --cov --cov-fail-under=80
    ↓
（main 分支）
[deploy]      ssh 到 VPS 执行部署脚本
```

所有步骤串行，任一失败阻断后续。

---

## 部署方案

### systemd unit（`deploy/systemd/html-host.service`）

```ini
[Unit]
Description=html-host API
After=network.target

[Service]
User=html-host
WorkingDirectory=/opt/html-host
EnvironmentFile=/opt/html-host/.env
ExecStart=/opt/html-host/.venv/bin/uvicorn html_host.main:app --host 127.0.0.1 --port 8001
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### nginx（`deploy/nginx/html-host.conf`）

```nginx
# 上传页面
location /html-upload/ {
    alias /var/www/html-upload/;
    index index.html;
}

# API 反代
location /html-upload-api/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# 托管上传的 HTML 文件
location /html/ {
    alias /var/www/html-host/;
    default_type text/html;
}
```

### Makefile 常用命令

```makefile
install     # uv sync 安装依赖
dev         # 本地启动开发服务器
test        # 运行测试
test-cov    # 运行测试 + 覆盖率
lint        # ruff check
format      # ruff format
typecheck   # basedpyright
migrate     # alembic upgrade head
deploy      # 推送并在 VPS 执行部署
```

---

## 迭代规划

### v1.0（MVP）
- [x] 文件上传、短链接生成
- [x] 文件列表、删除
- [x] Bearer Token 认证
- [x] systemd + nginx 部署

### v1.1（可选增强）
- [ ] 上传文件过期时间（TTL）
- [ ] 文件访问次数统计

### v2.0（如需多用户）
- [ ] 用户系统（此时引入 PostgreSQL）
- [ ] API Key 管理界面

---

## 本地开发流程

```bash
git clone git@github.com:xxx/html-host.git
cd html-host/backend
cp ../../.env.example .env   # 填入本地配置
make install                 # 安装依赖
make migrate                 # 初始化数据库
make dev                     # 启动开发服务器，访问 http://localhost:8001/docs
make test                    # 运行测试
```

FastAPI 自动生成 `/docs`（Swagger UI），本地开发可直接在浏览器里测试所有接口，无需 Postman。

---

## 类型系统

### 类型检查器选型

**推荐：basedpyright（当前），关注 ty（未来）**

主流选项对比（数据截至 2026 年 5 月）：

| 工具 | 速度 | Typing Spec 符合率 | nvim LSP | 状态 | 结论 |
|---|---|---|---|---|---|
| **basedpyright** | 快 | ~98% | ✅ nvim-lspconfig 原生 | 稳定，双周发布 | **现阶段推荐** |
| pyright | 快 | ~98% | ✅ 原生 | 稳定 | basedpyright 是其超集，直接选后者 |
| **ty** | 极快（Rust，10-60x） | **53%** | ✅ nvim-lspconfig 已支持 | **beta** | 潜力最大，但符合率太低，暂不用于生产 |
| mypy | 慢 | ~58% | ⚠️ 需插件 | 稳定 | 速度和推断能力均被 pyright 系超越 |
| pylance | 快 | ~98% | ❌ 仅 VS Code | 稳定 | nvim 不可用 |
| pyrefly | 极快（Rust） | 参见注 | ⚠️ 早期 | alpha | Meta 出品，与 ty 同期竞争 |

**为什么选 basedpyright 而不是 ty（2026 年 5 月的判断）**：

ty 目前是 **beta**，Typing Spec 符合率仅 **53%**，远低于 pyright/basedpyright 的 98%。这意味着大量合法的类型错误会被漏报，或者合法代码被误报。速度再快，在严格工程化项目中这是不可接受的。

basedpyright 是 pyright 的社区 fork，双周跟进上游，额外增加了 `reportAny` 等更严格规则和更好的报错信息，nvim 配置与 pyright 完全一致。

**ty 值得持续关注**：nvim-lspconfig 已有 `lsp/ty.lua`，Astral 团队的执行力有目共睹（ruff、uv 都做到了行业标准）。ty 1.0 stable 发布后符合率补齐，迁移成本极低（改一行配置）。

### 类型注解规范

使用 Python 3.12+ 原生语法，不引入 `typing` 模块的旧式写法：

```python
# ✅ 现代写法（Python 3.10+）
def process(items: list[str]) -> dict[str, int]: ...
def find(id: int) -> FileRecord | None: ...

# ❌ 旧式写法，不用
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]: ...
def find(id: int) -> Optional[FileRecord]: ...
```

纯类型导入放入 `TYPE_CHECKING` 块，避免运行时循环导入：

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
```

`__init__.py` 中 re-export 用 `X as X`：

```python
# html_host/api/v1/__init__.py
from html_host.api.v1.router import router as router
```

### pyproject.toml 配置

```toml
[tool.basedpyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingImports = true
reportAny = true

[tool.ruff]
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
# UP: pyupgrade，自动提示旧式类型注解
```

---

## 开发环境

### Python 工具链

| 工具 | 版本要求 | 用途 |
|---|---|---|
| Python | 3.12+ | 运行时 |
| uv | latest | 包管理、虚拟环境、lockfile |
| pre-commit | latest | 提交前自动运行 lint + 类型检查 |

### 虚拟环境

```bash
cd backend
uv sync        # 创建 .venv，安装所有依赖（含 dev）
uv sync --no-dev  # 生产环境，不装 dev 依赖
```

---

### pre-commit hooks（`.pre-commit-config.yaml`）

每次 `git commit` 前自动执行，本地拦截问题，不依赖 CI：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff          # lint，自动修复
        args: [--fix]
      - id: ruff-format   # 格式化

  - repo: local
    hooks:
      - id: basedpyright
        name: basedpyright
        entry: uv run basedpyright
        language: system
        types: [python]
        pass_filenames: false
```

安装：`pre-commit install`（首次 clone 后执行一次）

### 编辑器配置（`.editorconfig`）

统一缩进、换行符，避免不同编辑器产生无意义 diff：

```ini
root = true
[*.py]
indent_style = space
indent_size = 4
end_of_line = lf
trim_trailing_whitespace = true
```

### 环境隔离

- `.env` 文件本地使用，**永远不提交到 git**（`.gitignore` 中列出）
- `.env.example` 提交到 git，作为配置模板，所有字段有注释说明
- 本地 SQLite 数据库路径指向项目目录内，与生产环境完全隔离

---

## 代码仓库

### 平台

GitHub，Private 仓库。

### 分支策略（Trunk-based Development）

个人项目采用主干开发，简单高效：

```
main（受保护，只能通过 PR 合并）
  └── feature/xxx    功能分支，开发完立即合并，不长期存在
  └── fix/xxx        修复分支
```

- `main` 分支始终保持可部署状态
- 功能分支生命周期不超过 2 天，避免长期分叉
- 直接推送 `main` 被禁止，必须通过 PR

### Commit 规范（Conventional Commits）

```
<type>(<scope>): <subject>

type:
  feat     新功能
  fix      修复
  refactor 重构（不改变行为）
  test     测试
  chore    构建/工具/依赖
  docs     文档

示例：
feat(api): add file upload endpoint
fix(auth): return 401 instead of 500 on invalid token
chore(deps): bump fastapi to 0.111
```

规范 commit message 是为了：
1. `git log` 可读
2. 未来可用工具自动生成 CHANGELOG

### PR 规范

- PR 标题遵循 Conventional Commits 格式
- 合并前必须 CI 全部通过
- 小 PR 原则：单个 PR 只做一件事，diff 控制在 400 行以内

### GitHub 仓库设置

```
Settings → Branches → Branch protection rules (main):
  ✅ Require status checks to pass (lint, typecheck, test)
  ✅ Require branches to be up to date before merging
  ✅ Do not allow bypassing the above settings
```

### `.gitignore` 关键条目

```
.env
*.db
.venv/
__pycache__/
.pytest_cache/
htmlcov/
dist/
```

---

## DevOps（CI/CD）

### 流水线全貌

```
触发条件：push 到任意分支 / PR 到 main
                    │
         ┌──────────▼──────────┐
         │    [ci] 质量门控     │  所有分支都跑
         │  lint → type → test  │
         └──────────┬──────────┘
                    │ 仅 main 分支
         ┌──────────▼──────────┐
         │   [deploy] 部署      │
         │  备份 → 更新 → 重启  │
         └─────────────────────┘
```

### GitHub Actions 工作流（`.github/workflows/ci.yml`）

```yaml
name: CI/CD

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
        working-directory: backend
      - run: uv run ruff check .
        working-directory: backend
      - run: uv run ruff format --check .
        working-directory: backend

  typecheck:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
        working-directory: backend
      - run: uv run basedpyright
        working-directory: backend

  test:
    needs: typecheck
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
        working-directory: backend
      - run: uv run pytest --cov --cov-fail-under=80 --cov-report=xml
        working-directory: backend
      - uses: codecov/codecov-action@v4   # 可选：覆盖率可视化
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/html-host
            git pull origin main
            uv sync --no-dev
            uv run alembic upgrade head
            sudo systemctl restart html-host
            sudo systemctl is-active html-host   # 重启失败则退出码非零，CI 标红
```

### GitHub Secrets 配置

| Secret | 内容 |
|---|---|
| `VPS_HOST` | `120.77.223.17` |
| `VPS_USER` | `html-host`（专用部署用户，非 root） |
| `VPS_SSH_KEY` | 部署专用 SSH 私钥（不复用个人密钥） |
| `CODECOV_TOKEN` | Codecov 集成 token（可选） |

### 部署策略

**当前阶段（v1）**：停机重启，可接受（个人工具，秒级停机无影响）

```
git pull → alembic upgrade head → systemctl restart
```

**未来（v2，如需零停机）**：
```
# 使用 gunicorn 替换 uvicorn，支持 graceful reload
systemctl reload html-host   # 不中断存量请求
```

### 回滚方案

```bash
# 在 VPS 上执行
cd /opt/html-host
git log --oneline -10            # 确认目标版本
git checkout <commit-hash>
uv sync --no-dev
uv run alembic downgrade -1      # 如有迁移需要回退
sudo systemctl restart html-host
```

迁移文件保证每个 upgrade 都有对应 downgrade，回滚不需要手动改数据库。

---

## 生产环境

### 服务账户隔离

不用 root 运行服务，创建专用系统用户：

```bash
useradd --system --no-create-home --shell /sbin/nologin html-host
chown -R html-host:html-host /opt/html-host /var/www/html-host
```

### 目录与权限

```
/opt/html-host/          # 应用代码，html-host 用户所有
  ├── .venv/
  ├── src/
  ├── .env                # 生产配置，chmod 600
  └── data.db             # SQLite 数据库

/var/www/html-host/      # 上传的 HTML 文件，nginx 读取
/var/www/html-upload/    # 上传页面静态文件，nginx 读取
```

### 日志管理

systemd 自动收集 stdout/stderr 到 journald：

```bash
journalctl -u html-host -f          # 实时查看
journalctl -u html-host --since today   # 今日日志
journalctl -u html-host -n 100      # 最近 100 行
```

应用层使用结构化日志（JSON 格式），便于后续接入日志平台：

```python
# 每次请求记录：时间、方法、路径、状态码、耗时
{"time": "...", "method": "POST", "path": "/v1/files", "status": 200, "ms": 42}
```

### 数据备份

SQLite 数据库每日备份（cron job）：

```bash
# /etc/cron.d/html-host-backup
0 3 * * * html-host sqlite3 /opt/html-host/data.db ".backup '/opt/html-host/backup/data-$(date +\%Y\%m\%d).db'"
```

保留最近 30 天，上传文件目录同步备份：

```bash
# 也可以用 rsync 推到另一台机器或对象存储（OSS）
```

### 健康检查

`GET /health` 无需认证，返回服务状态。systemd 可配置健康检查：

```ini
[Service]
ExecStartPost=/bin/sleep 2
ExecStartPost=/usr/bin/curl -sf http://127.0.0.1:8001/health
```

启动后自动验证服务可用，不可用则 systemd 标记为启动失败并触发 Restart。

### nginx 安全加固

```nginx
# 限制上传请求体大小（与应用层配置保持一致）
location /html-upload-api/ {
    client_max_body_size 2m;
    ...
}

# 上传的 HTML 文件禁止执行脚本（纯静态托管）
location /html/ {
    alias /var/www/html-host/;
    default_type text/html;
    add_header X-Content-Type-Options nosniff;
    add_header Content-Security-Policy "default-src 'self'";
}
```

### 监控（轻量方案）

当前阶段不引入 Prometheus/Grafana 等重型方案，用以下轻量手段：

| 手段 | 工具 |
|---|---|
| 服务存活 | systemd Restart=on-failure 自动拉起 |
| 接口可用性 | UptimeRobot 免费计划，每 5 分钟 ping `/health` |
| 异常告警 | UptimeRobot 不可用时发邮件通知 |

---

## 完整生命周期总结

```
本地开发
  pre-commit hooks 本地拦截问题
  make dev / make test 本地验证
        │
        │  git push feature/xxx
        ▼
GitHub PR
  CI 自动运行（lint → typecheck → test）
  全部通过才允许合并
        │
        │  合并到 main
        ▼
GitHub Actions deploy job
  SSH 到 VPS
  git pull → migrate → restart
  验证 systemctl is-active
        │
        ▼
生产环境
  systemd 保证进程存活
  nginx 处理 HTTPS + 反代
  journald 收集日志
  cron 每日备份数据库
  UptimeRobot 监控可用性
```
