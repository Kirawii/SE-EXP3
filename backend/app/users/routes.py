from fastapi import APIRouter, Depends

from ..deps import get_current_user_id
from .repository import get_user_by_id, update_profile
from .schemas import ProfileUpdateIn, UserPublicOut


router = APIRouter()


def _to_public(data: dict) -> UserPublicOut:
    return UserPublicOut(
        id=data["id"],
        username=data["username"],
        email=data.get("email"),
        role=data.get("role", "USER"),
        nickname=data.get("nickname"),
        avatar=data.get("avatar"),
        created_at=data.get("created_at", ""),
    )


@router.get("/me", response_model=UserPublicOut)
async def me(uid: str = Depends(get_current_user_id)) -> UserPublicOut:
    return _to_public(await get_user_by_id(uid))


@router.patch("/me", response_model=UserPublicOut)
async def update_me(payload: ProfileUpdateIn, uid: str = Depends(get_current_user_id)) -> UserPublicOut:
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    return _to_public(await update_profile(uid, fields))
