from fastapi import APIRouter, Depends

from ..deps import get_current_user_id
from ..landmarks.schemas import LandmarkOut
from ..social.repository import list_favorites
from .repository import get_user_by_id, update_profile
from .schemas import ProfileUpdateIn, UserPublicOut


router = APIRouter()


@router.get("/me/favorites", response_model=list[LandmarkOut])
async def my_favorites(uid: str = Depends(get_current_user_id)) -> list[dict]:
    return await list_favorites(uid)


def to_public(data: dict) -> UserPublicOut:
    return UserPublicOut(
        id=data["id"],
        username=data["username"],
        email=data.get("email"),
        role=data.get("role", "USER"),
        nickname=data.get("nickname"),
        avatar=data.get("avatar"),
        disabled=data.get("disabled") == "1",
        created_at=data.get("created_at", ""),
    )


# 向后兼容的内部别名
_to_public = to_public


@router.get("/me", response_model=UserPublicOut)
async def me(uid: str = Depends(get_current_user_id)) -> UserPublicOut:
    return _to_public(await get_user_by_id(uid))


@router.patch("/me", response_model=UserPublicOut)
async def update_me(payload: ProfileUpdateIn, uid: str = Depends(get_current_user_id)) -> UserPublicOut:
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    return _to_public(await update_profile(uid, fields))
