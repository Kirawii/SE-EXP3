from __future__ import annotations

import time

from ..config import get_settings
from ..errors import Forbidden, NotFound
from ..redis_client import K, redis


def _to_out(d: dict) -> dict:
    return {
        "id": d["id"],
        "name": d.get("name", ""),
        "category": d.get("category", ""),
        "description": d.get("description", ""),
        "image_url": d.get("image_url") or None,
        "owner_id": d["owner_id"],
        "status": d.get("status", "APPROVED"),
        "lng": float(d["lng"]),
        "lat": float(d["lat"]),
        "created_at": d.get("created_at", ""),
        "updated_at": d.get("updated_at", d.get("created_at", "")),
    }


async def get_next_landmark_id() -> str:
    return str(await redis().incr(K.SEQ_LANDMARK))


async def create_landmark(
    *,
    owner_id: str,
    name: str,
    category: str,
    description: str,
    image_url: str | None,
    lng: float,
    lat: float,
) -> dict:
    settings = get_settings()
    r = redis()

    lid = await get_next_landmark_id()
    now = str(int(time.time()))
    status = "APPROVED" if settings.landmark_auto_approve else "PENDING"
    mapping = {
        "id": lid,
        "name": name,
        "category": category,
        "description": description,
        "image_url": image_url or "",
        "owner_id": owner_id,
        "status": status,
        "lng": str(lng),
        "lat": str(lat),
        "created_at": now,
        "updated_at": now,
    }

    pipe = r.pipeline()
    pipe.hset(K.landmark(lid), mapping=mapping)
    pipe.sadd(K.landmark_by_owner(owner_id), lid)
    pipe.sadd(K.landmark_by_status(status), lid)
    pipe.sadd(K.landmark_by_category(category), lid)
    if status == "APPROVED":
        pipe.geoadd(settings.default_geo_key, [lng, lat, lid])
    await pipe.execute()
    return _to_out(mapping)


async def get_landmark(lid: str) -> dict:
    raw = await redis().hgetall(K.landmark(lid))
    if not raw:
        raise NotFound("地标不存在")
    return _to_out(raw)


async def update_landmark(
    lid: str, requester_id: str, requester_role: str, fields: dict
) -> dict:
    settings = get_settings()
    r = redis()

    raw = await r.hgetall(K.landmark(lid))
    if not raw:
        raise NotFound("地标不存在")
    if raw["owner_id"] != requester_id and requester_role != "ADMIN":
        raise Forbidden("仅作者或管理员可修改")

    new_data = dict(raw)
    pipe = r.pipeline()

    if "category" in fields:
        old_cat = raw.get("category", "")
        if old_cat:
            pipe.srem(K.landmark_by_category(old_cat), lid)
        pipe.sadd(K.landmark_by_category(fields["category"]), lid)
        new_data["category"] = fields["category"]

    if "status" in fields and fields["status"] != raw.get("status"):
        old_status = raw.get("status", "PENDING")
        pipe.srem(K.landmark_by_status(old_status), lid)
        pipe.sadd(K.landmark_by_status(fields["status"]), lid)
        new_data["status"] = fields["status"]
        if fields["status"] == "APPROVED":
            pipe.geoadd(
                settings.default_geo_key,
                [float(new_data["lng"]), float(new_data["lat"]), lid],
            )
        else:
            pipe.zrem(settings.default_geo_key, lid)

    if "lng" in fields or "lat" in fields:
        new_lng = float(fields.get("lng", raw["lng"]))
        new_lat = float(fields.get("lat", raw["lat"]))
        new_data["lng"] = str(new_lng)
        new_data["lat"] = str(new_lat)
        if new_data.get("status", raw.get("status")) == "APPROVED":
            pipe.geoadd(settings.default_geo_key, [new_lng, new_lat, lid])

    for key in ("name", "description", "image_url"):
        if key in fields:
            new_data[key] = fields[key] if fields[key] is not None else ""

    new_data["updated_at"] = str(int(time.time()))
    pipe.hset(
        K.landmark(lid),
        mapping={
            "name": new_data.get("name", ""),
            "category": new_data.get("category", ""),
            "description": new_data.get("description", ""),
            "image_url": new_data.get("image_url", "") or "",
            "lng": new_data["lng"],
            "lat": new_data["lat"],
            "status": new_data.get("status", "APPROVED"),
            "updated_at": new_data["updated_at"],
        },
    )
    await pipe.execute()
    return _to_out(new_data)


async def delete_landmark(lid: str, requester_id: str, requester_role: str) -> None:
    settings = get_settings()
    r = redis()
    raw = await r.hgetall(K.landmark(lid))
    if not raw:
        raise NotFound("地标不存在")
    if raw["owner_id"] != requester_id and requester_role != "ADMIN":
        raise Forbidden("仅作者或管理员可删除")

    pipe = r.pipeline()
    pipe.delete(K.landmark(lid))
    pipe.srem(K.landmark_by_owner(raw["owner_id"]), lid)
    if raw.get("status"):
        pipe.srem(K.landmark_by_status(raw["status"]), lid)
    if raw.get("category"):
        pipe.srem(K.landmark_by_category(raw["category"]), lid)
    pipe.zrem(settings.default_geo_key, lid)
    await pipe.execute()


async def list_by_owner(owner_id: str) -> list[dict]:
    return await _hydrate_set(K.landmark_by_owner(owner_id))


async def list_by_category(cat: str) -> list[dict]:
    return await _hydrate_set(K.landmark_by_category(cat))


async def list_by_status(status: str) -> list[dict]:
    return await _hydrate_set(K.landmark_by_status(status))


async def search_landmarks(
    *, q: str | None = None, category: str | None = None, status: str = "APPROVED", limit: int = 100
) -> list[dict]:
    """按状态/类别取候选集合，再在应用层按名称关键字过滤。原型规模下足够。"""
    if category:
        base = K.landmark_by_category(category)
    else:
        base = K.landmark_by_status(status)

    ids = list(await redis().smembers(base))
    rows = await hydrate_many(ids)

    # 指定类别时仍需用状态二次过滤（类别集合含各种状态）
    if category:
        rows = [r for r in rows if r["status"] == status]
    if q:
        kw = q.strip().lower()
        rows = [r for r in rows if kw in r["name"].lower()]

    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows[:limit]


async def hydrate_many(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    r = redis()
    pipe = r.pipeline()
    for lid in ids:
        pipe.hgetall(K.landmark(lid))
    rows = await pipe.execute()
    return [_to_out(row) for row in rows if row]


async def _hydrate_set(set_key: str) -> list[dict]:
    r = redis()
    ids = list(await r.smembers(set_key))
    if not ids:
        return []
    return await hydrate_many(ids)
