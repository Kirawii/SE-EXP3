from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from ..config import get_settings
from ..deps import client_ip, get_current_payload
from ..errors import Forbidden, InvalidCredentials, NotFound, TooManyRequests
from ..redis_client import K, redis
from ..security import hash_password, issue_token, verify_password
from ..users.repository import create_user, get_user_by_username
from .schemas import LoginIn, RegisterIn, TokenOut, UserOut


router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn) -> UserOut:
    return await create_user(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request) -> TokenOut:
    settings = get_settings()
    r = redis()

    rate_key = K.login_rate(client_ip(request))
    pipe = r.pipeline()
    pipe.incr(rate_key)
    pipe.expire(rate_key, settings.login_rate_window_seconds)
    count, _ = await pipe.execute()
    if int(count) > settings.login_rate_limit:
        raise TooManyRequests("登录尝试过于频繁，请稍后再试")

    try:
        user = await get_user_by_username(payload.username)
    except NotFound:
        raise InvalidCredentials("用户名或密码错误")
    if not verify_password(payload.password, user.get("password_hash", "")):
        raise InvalidCredentials("用户名或密码错误")
    if user.get("disabled") == "1":
        raise Forbidden("账号已被禁用，请联系管理员")

    token, _, exp = issue_token(user["id"], user.get("role", "USER"))
    return TokenOut(
        access_token=token,
        expires_at=exp.isoformat(),
        user=UserOut(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user.get("role", "USER"),
            nickname=user.get("nickname") or None,
            avatar=user.get("avatar") or None,
            created_at=user.get("created_at", ""),
        ),
    )


@router.post("/logout", status_code=204)
async def logout(payload: dict = Depends(get_current_payload)) -> None:
    jti = payload["jti"]
    exp = int(payload.get("exp", 0))
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp - now, 1)
    await redis().set(K.auth_revoked(jti), "1", ex=ttl)
