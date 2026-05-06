"""端到端冒烟：注册 → 登录 → 创建地标 → GEO 查询 → 登出 → 401。"""

import pytest


pytestmark = pytest.mark.asyncio


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_register_login_create_geo_logout(client):
    # 1. 注册
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "Password1",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["username"] == "alice"

    # 2. 登录
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "Password1"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. /me
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"

    # 4. 创建地标 A（天安门）
    resp = await client.post(
        "/api/v1/landmarks",
        headers=headers,
        json={
            "name": "天安门",
            "category": "history",
            "description": "广场",
            "image_url": None,
            "lng": 116.397,
            "lat": 39.908,
        },
    )
    assert resp.status_code == 201, resp.text
    a_id = resp.json()["id"]

    # 5. 创建地标 B（颐和园）
    resp = await client.post(
        "/api/v1/landmarks",
        headers=headers,
        json={
            "name": "颐和园",
            "category": "park",
            "description": "皇家园林",
            "image_url": None,
            "lng": 116.310,
            "lat": 39.992,
        },
    )
    assert resp.status_code == 201, resp.text
    b_id = resp.json()["id"]

    # 6. 近邻查询：以天安门为中心 20 km
    resp = await client.get(
        "/api/v1/geo/nearby",
        params={"lng": 116.397, "lat": 39.908, "radius_km": 20},
    )
    assert resp.status_code == 200
    hits = resp.json()
    assert len(hits) >= 2
    assert {h["id"] for h in hits} >= {a_id, b_id}

    # 7. 距离计算：约 14 km
    resp = await client.get(f"/api/v1/geo/distance?a={a_id}&b={b_id}")
    assert resp.status_code == 200
    d = resp.json()["distance_km"]
    assert 10 < d < 20, f"distance {d} not in expected range"

    # 8. Geohash
    resp = await client.get(f"/api/v1/geo/geohash/{a_id}")
    assert resp.status_code == 200
    assert len(resp.json()["geohash"]) > 0

    # 9. 矩形查询
    resp = await client.get(
        "/api/v1/geo/box",
        params={"lng": 116.35, "lat": 39.95, "width_km": 30, "height_km": 30},
    )
    assert resp.status_code == 200
    box_hits = resp.json()
    assert {h["id"] for h in box_hits} >= {a_id, b_id}

    # 10. 我的地标
    resp = await client.get("/api/v1/landmarks/mine", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # 11. 登出
    resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 204

    # 12. 吊销后访问 /me 应 401
    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["code"] == "token_revoked"


async def test_register_duplicate(client):
    payload = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "Password1",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["code"] == "username_taken"


async def test_login_invalid(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "carol",
            "email": "carol@example.com",
            "password": "Password1",
        },
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"username": "carol", "password": "wrong-pwd"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "invalid_credentials"


async def test_landmark_owner_only_update(client):
    # alice 创建，bob 尝试改 → 403
    await client.post(
        "/api/v1/auth/register",
        json={"username": "alice2", "email": "a2@ex.com", "password": "Password1"},
    )
    await client.post(
        "/api/v1/auth/register",
        json={"username": "bob2", "email": "b2@ex.com", "password": "Password1"},
    )
    a_login = await client.post(
        "/api/v1/auth/login", json={"username": "alice2", "password": "Password1"}
    )
    b_login = await client.post(
        "/api/v1/auth/login", json={"username": "bob2", "password": "Password1"}
    )
    a_h = {"Authorization": f"Bearer {a_login.json()['access_token']}"}
    b_h = {"Authorization": f"Bearer {b_login.json()['access_token']}"}

    create_resp = await client.post(
        "/api/v1/landmarks",
        headers=a_h,
        json={
            "name": "test",
            "category": "x",
            "description": "",
            "image_url": None,
            "lng": 100.0,
            "lat": 30.0,
        },
    )
    lid = create_resp.json()["id"]

    forbidden = await client.patch(
        f"/api/v1/landmarks/{lid}",
        headers=b_h,
        json={"name": "hacked"},
    )
    assert forbidden.status_code == 403

    ok = await client.patch(
        f"/api/v1/landmarks/{lid}",
        headers=a_h,
        json={"name": "renamed"},
    )
    assert ok.status_code == 200
    assert ok.json()["name"] == "renamed"
