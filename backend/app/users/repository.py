from __future__ import annotations

import time

from ..auth.schemas import UserOut
from ..errors import EmailTaken, NotFound, UsernameTaken
from ..redis_client import K, redis


async def get_next_user_id() -> str:
    return str(await redis().incr(K.SEQ_USER))


async def create_user(*, username: str, email: str, password_hash: str, role: str = "USER") -> UserOut:
    r = redis()
    uname_key = K.user_by_username(username)
    email_key = K.user_by_email(email)
    if await r.exists(uname_key):
        raise UsernameTaken("用户名已被占用")
    if await r.exists(email_key):
        raise EmailTaken("邮箱已被注册")

    uid = await get_next_user_id()
    now = str(int(time.time()))
    pipe = r.pipeline()
    pipe.hset(
        K.user(uid),
        mapping={
            "id": uid,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": now,
        },
    )
    pipe.set(uname_key, uid)
    pipe.set(email_key, uid)
    pipe.sadd(K.role_set(role), uid)
    await pipe.execute()
    return UserOut(id=uid, username=username, email=email, role=role, created_at=now)


async def get_user_by_id(uid: str) -> dict:
    data = await redis().hgetall(K.user(uid))
    if not data:
        raise NotFound("用户不存在")
    return data


async def get_user_by_username(username: str) -> dict:
    uid = await redis().get(K.user_by_username(username))
    if not uid:
        raise NotFound("用户不存在")
    return await get_user_by_id(uid)


async def update_profile(uid: str, fields: dict) -> dict:
    if fields:
        await redis().hset(K.user(uid), mapping=fields)
    return await get_user_by_id(uid)
