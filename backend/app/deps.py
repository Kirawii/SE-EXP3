from __future__ import annotations

import jwt as _jwt
from fastapi import Depends, Header, Request

from .errors import Forbidden, TokenInvalid, TokenRevoked
from .redis_client import K, redis
from .security import decode_token


async def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise TokenInvalid("缺少 Bearer Token")
    return authorization.split(" ", 1)[1].strip()


async def get_current_payload(token: str = Depends(get_bearer_token)) -> dict:
    try:
        payload = decode_token(token)
    except _jwt.ExpiredSignatureError:
        raise TokenInvalid("Token 已过期")
    except _jwt.PyJWTError:
        raise TokenInvalid("Token 解码失败")

    jti = payload.get("jti")
    if not jti:
        raise TokenInvalid("Token 缺少 jti")
    if await redis().exists(K.auth_revoked(jti)):
        raise TokenRevoked("Token 已被吊销")
    return payload


async def get_current_user(payload: dict = Depends(get_current_payload)) -> dict:
    return {
        "id": payload["sub"],
        "role": payload.get("role", "USER"),
        "jti": payload.get("jti"),
        "exp": int(payload.get("exp", 0)),
    }


async def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    return user["id"]


async def get_optional_user_id(authorization: str | None = Header(default=None)) -> str | None:
    """可选鉴权：带合法 Token 返回 uid，否则返回 None，不抛错。用于公开但需识别身份的接口。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except _jwt.PyJWTError:
        return None
    jti = payload.get("jti")
    if not jti or await redis().exists(K.auth_revoked(jti)):
        return None
    return payload.get("sub")


def require_role(*roles: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise Forbidden(f"需要角色：{','.join(roles)}")
        return user

    return checker


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
