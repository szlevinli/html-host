# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                          # install all deps (incl. dev)
uv sync --no-dev                 # production install
uv run uvicorn html_host.main:app --reload  # dev server → http://localhost:8000/docs
uv run pytest                    # all tests with coverage
uv run pytest tests/test_files_api.py::test_upload  # single test
uv run pytest --cov-fail-under=80  # enforce coverage gate
uv run ruff check .              # lint
uv run ruff format .             # format
uv run basedpyright              # type check
uv run alembic upgrade head      # apply migrations
uv run alembic revision --autogenerate -m "description"  # new migration
```

## Architecture

FastAPI service with a strict layered structure — each layer has one job:

```
api/v1/        ← HTTP boundary: routing, request/response shapes (Pydantic schemas)
services/      ← business logic, framework-agnostic
db/            ← base.py (DeclarativeBase only), session.py (engine + get_session), models.py, migrations/
core/          ← config (pydantic-settings) + auth (Bearer token dependency)
```

**Request flow:** `api/v1/files.py` → `services/file_service.py` → `db/models.py`

Business logic lives only in `services/`. API handlers are thin: validate input, call service, return response. Never put DB queries in route handlers.

**Unified response envelope** for all `/v1/*` endpoints:
```json
{ "data": {...}, "error": null }   // success
{ "data": null, "error": { "code": "...", "message": "..." } }  // failure
```

**Auth:** single Bearer token validated via a FastAPI `Depends()` in `core/security.py`, injected into every `/v1/*` route. `/health` is unauthenticated.

**Database:** SQLite + aiosqlite (async). Schema changes go through Alembic only — never `ALTER TABLE` manually. Every migration must have a working `downgrade()`.

## Key conventions

- `pyproject.toml` is the source of truth for ruff and basedpyright config — read it at session start.
- `src/` layout: the package is `src/html_host/`, installed editable via `uv sync`.
- Base URL: `/html-upload-api/v1` (versioned; nginx strips the prefix before forwarding to uvicorn).
- Uploaded HTML files are served statically by nginx from `UPLOAD_DIR`, not by FastAPI.
- `MAX_FILE_SIZE_MB` is enforced at both nginx (`client_max_body_size`) and application layer.
