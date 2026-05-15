import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"  # type: ignore[reportAny]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    r = await client.post("/v1/auth/login", json={"password": "test-password"})
    assert r.status_code == 200
    body = r.json()  # type: ignore[reportAny]
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    r = await client.post("/v1/auth/login", json={"password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient) -> None:
    r = await client.post(
        "/v1/files",
        files={"file": ("test.html", b"<h1>hi</h1>", "text/html")},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_upload_and_list(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    content = b"<h1>hello</h1>"
    r = await client.post(
        "/v1/files",
        files={"file": ("hello.html", content, "text/html")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()["data"]  # type: ignore[reportAny]
    assert data["filename"] == "hello.html"
    assert data["size_bytes"] == len(content)
    assert data["url"].endswith(data["short_code"])  # type: ignore[reportAny]

    r = await client.get("/v1/files", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1  # type: ignore[reportAny]


@pytest.mark.asyncio
async def test_delete(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post(
        "/v1/files",
        files={"file": ("del.html", b"<p>bye</p>", "text/html")},
        headers=auth_headers,
    )
    code = r.json()["data"]["short_code"]  # type: ignore[reportAny]

    r = await client.delete(f"/v1/files/{code}", headers=auth_headers)
    assert r.status_code == 200

    r = await client.delete(f"/v1/files/{code}", headers=auth_headers)
    assert r.status_code == 404
