from __future__ import annotations

from redis.asyncio import Redis, from_url

from .config import get_settings


_redis: Redis | None = None


async def init_redis() -> Redis:
    global _redis
    settings = get_settings()
    _redis = from_url(
        settings.redis_url,
        password=settings.redis_password or None,
        decode_responses=True,
        encoding="utf-8",
    )
    await _redis.ping()
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis 客户端尚未初始化")
    return _redis


class K:
    """Redis Key 命名空间。所有访问 Redis 的代码都从这里取 Key，避免散落字符串。"""

    SEQ_USER = "seq:users"
    SEQ_LANDMARK = "seq:landmarks"
    SEQ_COMMENT = "seq:comments"

    @staticmethod
    def user(uid: str) -> str:
        return f"users:{uid}"

    @staticmethod
    def user_by_username(name: str) -> str:
        return f"users:by_username:{name.lower()}"

    @staticmethod
    def user_by_email(email: str) -> str:
        return f"users:by_email:{email.lower()}"

    @staticmethod
    def role_set(role: str) -> str:
        return f"users:role:{role}"

    @staticmethod
    def auth_revoked(jti: str) -> str:
        return f"auth:revoked:{jti}"

    @staticmethod
    def login_rate(ip: str) -> str:
        return f"ratelimit:login:{ip}"

    @staticmethod
    def landmark(lid: str) -> str:
        return f"landmarks:{lid}"

    @staticmethod
    def landmark_by_owner(uid: str) -> str:
        return f"landmarks:by_owner:{uid}"

    @staticmethod
    def landmark_by_status(status: str) -> str:
        return f"landmarks:by_status:{status}"

    @staticmethod
    def landmark_by_category(cat: str) -> str:
        return f"landmarks:by_category:{cat}"

    # ---- 社交：收藏与评论 ----

    @staticmethod
    def fav_by_user(uid: str) -> str:
        """用户收藏的地标集合。"""
        return f"favorites:by_user:{uid}"

    @staticmethod
    def fav_by_landmark(lid: str) -> str:
        """收藏某地标的用户集合，用于计数。"""
        return f"favorites:by_landmark:{lid}"

    @staticmethod
    def comment(cid: str) -> str:
        return f"comments:{cid}"

    @staticmethod
    def comments_of(lid: str) -> str:
        """地标下的评论：Sorted Set，member=cid，score=created_at。"""
        return f"comments:by_landmark:{lid}"
