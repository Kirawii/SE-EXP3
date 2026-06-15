from __future__ import annotations

import time

from ..errors import Forbidden, NotFound
from ..redis_client import K, redis
from ..landmarks.repository import hydrate_many


# ---- 收藏 ----


async def _assert_landmark_exists(lid: str) -> None:
    if not await redis().exists(K.landmark(lid)):
        raise NotFound("地标不存在")


async def add_favorite(uid: str, lid: str) -> dict:
    await _assert_landmark_exists(lid)
    r = redis()
    pipe = r.pipeline()
    pipe.sadd(K.fav_by_user(uid), lid)
    pipe.sadd(K.fav_by_landmark(lid), uid)
    await pipe.execute()
    count = await r.scard(K.fav_by_landmark(lid))
    return {"landmark_id": lid, "favorited": True, "count": count}


async def remove_favorite(uid: str, lid: str) -> dict:
    r = redis()
    pipe = r.pipeline()
    pipe.srem(K.fav_by_user(uid), lid)
    pipe.srem(K.fav_by_landmark(lid), uid)
    await pipe.execute()
    count = await r.scard(K.fav_by_landmark(lid))
    return {"landmark_id": lid, "favorited": False, "count": count}


async def favorite_state(uid: str | None, lid: str) -> dict:
    r = redis()
    count = await r.scard(K.fav_by_landmark(lid))
    favorited = bool(uid) and await r.sismember(K.fav_by_landmark(lid), uid)
    return {"landmark_id": lid, "favorited": bool(favorited), "count": count}


async def list_favorites(uid: str) -> list[dict]:
    ids = list(await redis().smembers(K.fav_by_user(uid)))
    rows = await hydrate_many(ids)
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows


# ---- 评论 ----


async def add_comment(uid: str, username: str, lid: str, content: str) -> dict:
    await _assert_landmark_exists(lid)
    r = redis()
    cid = str(await r.incr(K.SEQ_COMMENT))
    now = int(time.time())
    mapping = {
        "id": cid,
        "landmark_id": lid,
        "user_id": uid,
        "username": username,
        "content": content,
        "created_at": str(now),
    }
    pipe = r.pipeline()
    pipe.hset(K.comment(cid), mapping=mapping)
    pipe.zadd(K.comments_of(lid), {cid: now})
    await pipe.execute()
    return mapping


async def list_comments(lid: str, limit: int = 100) -> list[dict]:
    r = redis()
    # 按时间倒序取评论 id
    cids = await r.zrevrange(K.comments_of(lid), 0, limit - 1)
    if not cids:
        return []
    pipe = r.pipeline()
    for cid in cids:
        pipe.hgetall(K.comment(cid))
    rows = await pipe.execute()
    return [row for row in rows if row]


async def delete_comment(cid: str, requester_id: str, requester_role: str) -> None:
    r = redis()
    raw = await r.hgetall(K.comment(cid))
    if not raw:
        raise NotFound("评论不存在")
    if raw["user_id"] != requester_id and requester_role != "ADMIN":
        raise Forbidden("仅作者或管理员可删除评论")
    pipe = r.pipeline()
    pipe.delete(K.comment(cid))
    pipe.zrem(K.comments_of(raw["landmark_id"]), cid)
    await pipe.execute()
