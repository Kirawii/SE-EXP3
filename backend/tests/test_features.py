"""收藏、评论、检索、管理后台的接口测试。"""

import pytest


pytestmark = pytest.mark.asyncio


async def _register(client, username, *, password="Password1"):
    return await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": f"{username}@ex.com", "password": password},
    )


async def _login(client, username, *, password="Password1"):
    r = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    return r


async def _auth_header(client, username):
    r = await _login(client, username)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()["user"]


async def _make_landmark(client, headers, name="点位", category="park", lng=116.4, lat=39.9):
    r = await client.post(
        "/api/v1/landmarks",
        headers=headers,
        json={"name": name, "category": category, "description": "", "image_url": None, "lng": lng, "lat": lat},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_first_user_is_admin(client):
    r = await _register(client, "boss")
    assert r.status_code == 201
    _, user = await _auth_header(client, "boss")
    assert user["role"] == "ADMIN"

    await _register(client, "normal")
    _, u2 = await _auth_header(client, "normal")
    assert u2["role"] == "USER"


async def test_login_returns_user(client):
    await _register(client, "alice")
    r = await _login(client, "alice")
    body = r.json()
    assert body["user"]["username"] == "alice"
    assert "access_token" in body


async def test_search_by_keyword_and_category(client):
    await _register(client, "alice")
    h, _ = await _auth_header(client, "alice")
    await _make_landmark(client, h, name="天安门", category="history", lng=116.397, lat=39.908)
    await _make_landmark(client, h, name="颐和园", category="park", lng=116.310, lat=39.992)

    r = await client.get("/api/v1/landmarks", params={"q": "天安"})
    assert r.status_code == 200
    names = [x["name"] for x in r.json()]
    assert names == ["天安门"]

    r = await client.get("/api/v1/landmarks", params={"category": "park"})
    assert [x["name"] for x in r.json()] == ["颐和园"]


async def test_favorite_flow(client):
    await _register(client, "alice")
    h, _ = await _auth_header(client, "alice")
    lm = await _make_landmark(client, h)

    # 收藏
    r = await client.put(f"/api/v1/landmarks/{lm['id']}/favorite", headers=h)
    assert r.status_code == 200
    assert r.json() == {"landmark_id": lm["id"], "favorited": True, "count": 1}

    # 我的收藏
    r = await client.get("/api/v1/users/me/favorites", headers=h)
    assert {x["id"] for x in r.json()} == {lm["id"]}

    # 取消收藏
    r = await client.delete(f"/api/v1/landmarks/{lm['id']}/favorite", headers=h)
    assert r.json()["favorited"] is False
    assert r.json()["count"] == 0

    r = await client.get("/api/v1/users/me/favorites", headers=h)
    assert r.json() == []


async def test_comment_flow(client):
    await _register(client, "alice")
    await _register(client, "bob")
    ha, _ = await _auth_header(client, "alice")
    hb, _ = await _auth_header(client, "bob")
    lm = await _make_landmark(client, ha)

    r = await client.post(
        f"/api/v1/landmarks/{lm['id']}/comments", headers=hb, json={"content": "很棒的地方"}
    )
    assert r.status_code == 201
    cid = r.json()["id"]
    assert r.json()["username"] == "bob"

    r = await client.get(f"/api/v1/landmarks/{lm['id']}/comments")
    assert len(r.json()) == 1

    # 非作者非管理员不能删
    r = await client.delete(f"/api/v1/comments/{cid}", headers=ha)
    # alice 是首个用户 = ADMIN，可以删
    assert r.status_code == 204
    r = await client.get(f"/api/v1/landmarks/{lm['id']}/comments")
    assert r.json() == []


async def test_recommend_ranks_by_distance_and_popularity(client):
    await _register(client, "alice")
    await _register(client, "bob")
    ha, _ = await _auth_header(client, "alice")
    hb, _ = await _auth_header(client, "bob")

    # 近的（天安门附近）与稍远但热门的（颐和园被收藏）
    near = await _make_landmark(client, ha, name="近店", category="shop", lng=116.398, lat=39.909)
    pop = await _make_landmark(client, ha, name="热门店", category="shop", lng=116.360, lat=39.940)

    # 给“热门店”刷收藏
    await client.put(f"/api/v1/landmarks/{pop['id']}/favorite", headers=ha)
    await client.put(f"/api/v1/landmarks/{pop['id']}/favorite", headers=hb)

    r = await client.get(
        "/api/v1/geo/recommend",
        params={"lng": 116.397, "lat": 39.908, "radius_km": 10},
    )
    assert r.status_code == 200
    hits = r.json()
    ids = {h["id"] for h in hits}
    assert {near["id"], pop["id"]} <= ids
    # 每条都带 popularity 与 score，且按 score 降序
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)
    pop_hit = next(h for h in hits if h["id"] == pop["id"])
    assert pop_hit["popularity"] == 2

    # 类别过滤
    r = await client.get(
        "/api/v1/geo/recommend",
        params={"lng": 116.397, "lat": 39.908, "radius_km": 10, "category": "shop"},
    )
    assert all(h["category"] == "shop" for h in r.json())


async def test_admin_review_pending(client, monkeypatch):
    # 关闭自动审核，让新地标进入 PENDING
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LANDMARK_AUTO_APPROVE", "false")

    await _register(client, "admin")  # 首个 = ADMIN
    await _register(client, "user")
    ha, _ = await _auth_header(client, "admin")
    hu, _ = await _auth_header(client, "user")

    lm = await _make_landmark(client, hu)
    assert lm["status"] == "PENDING"

    # 审核前 GEO 查询不到
    r = await client.get("/api/v1/geo/nearby", params={"lng": 116.4, "lat": 39.9, "radius_km": 5})
    assert lm["id"] not in {x["id"] for x in r.json()}

    # 管理员审核通过
    r = await client.get("/api/v1/admin/landmarks", params={"status": "PENDING"}, headers=ha)
    assert lm["id"] in {x["id"] for x in r.json()}
    r = await client.post(
        f"/api/v1/admin/landmarks/{lm['id']}/review", headers=ha, json={"action": "approve"}
    )
    assert r.json()["status"] == "APPROVED"

    # 审核后 GEO 可查
    r = await client.get("/api/v1/geo/nearby", params={"lng": 116.4, "lat": 39.9, "radius_km": 5})
    assert lm["id"] in {x["id"] for x in r.json()}

    get_settings.cache_clear()


async def test_admin_only(client):
    await _register(client, "admin")
    await _register(client, "user")
    hu, _ = await _auth_header(client, "user")
    r = await client.get("/api/v1/admin/users", headers=hu)
    assert r.status_code == 403


async def test_admin_disable_blocks_login(client):
    await _register(client, "admin")
    await _register(client, "victim")
    ha, _ = await _auth_header(client, "admin")
    _, victim = await _auth_header(client, "victim")

    r = await client.post(f"/api/v1/admin/users/{victim['id']}/disable", headers=ha)
    assert r.status_code == 200
    assert r.json()["disabled"] is True

    r = await _login(client, "victim")
    assert r.status_code == 403

    # 恢复后可登录
    r = await client.post(f"/api/v1/admin/users/{victim['id']}/enable", headers=ha)
    assert r.json()["disabled"] is False
    r = await _login(client, "victim")
    assert r.status_code == 200


async def test_cannot_disable_admin(client):
    await _register(client, "admin")
    ha, admin = await _auth_header(client, "admin")
    r = await client.post(f"/api/v1/admin/users/{admin['id']}/disable", headers=ha)
    assert r.status_code == 403
