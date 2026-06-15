from fastapi import APIRouter, Depends

from ..deps import get_current_user, get_optional_user_id
from ..users.repository import get_user_by_id
from .repository import (
    add_comment,
    add_favorite,
    delete_comment,
    favorite_state,
    list_comments,
    remove_favorite,
)
from .schemas import CommentCreateIn, CommentOut, FavoriteState


router = APIRouter()


# ---- 收藏 ----


@router.get("/landmarks/{lid}/favorite", response_model=FavoriteState)
async def get_favorite(lid: str, uid: str | None = Depends(get_optional_user_id)) -> dict:
    return await favorite_state(uid, lid)


@router.put("/landmarks/{lid}/favorite", response_model=FavoriteState)
async def put_favorite(lid: str, user: dict = Depends(get_current_user)) -> dict:
    return await add_favorite(user["id"], lid)


@router.delete("/landmarks/{lid}/favorite", response_model=FavoriteState)
async def del_favorite(lid: str, user: dict = Depends(get_current_user)) -> dict:
    return await remove_favorite(user["id"], lid)


# ---- 评论 ----


@router.get("/landmarks/{lid}/comments", response_model=list[CommentOut])
async def get_comments(lid: str) -> list[dict]:
    return await list_comments(lid)


@router.post("/landmarks/{lid}/comments", response_model=CommentOut, status_code=201)
async def post_comment(
    lid: str, payload: CommentCreateIn, user: dict = Depends(get_current_user)
) -> dict:
    profile = await get_user_by_id(user["id"])
    username = profile.get("nickname") or profile.get("username", "用户")
    return await add_comment(user["id"], username, lid, payload.content)


@router.delete("/comments/{cid}", status_code=204)
async def remove_comment(cid: str, user: dict = Depends(get_current_user)) -> None:
    await delete_comment(cid, user["id"], user["role"])
