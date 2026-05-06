from fastapi import APIRouter, Depends

from ..deps import get_current_user
from .repository import (
    create_landmark,
    delete_landmark,
    get_landmark,
    list_by_category,
    list_by_owner,
    update_landmark,
)
from .schemas import LandmarkCreateIn, LandmarkOut, LandmarkUpdateIn


router = APIRouter()


@router.post("", response_model=LandmarkOut, status_code=201)
async def create(payload: LandmarkCreateIn, user: dict = Depends(get_current_user)) -> dict:
    return await create_landmark(
        owner_id=user["id"],
        name=payload.name,
        category=payload.category,
        description=payload.description,
        image_url=payload.image_url,
        lng=payload.lng,
        lat=payload.lat,
    )


@router.get("/mine", response_model=list[LandmarkOut])
async def list_mine(user: dict = Depends(get_current_user)) -> list[dict]:
    return await list_by_owner(user["id"])


@router.get("/by-category/{category}", response_model=list[LandmarkOut])
async def list_by_cat(category: str) -> list[dict]:
    return await list_by_category(category)


@router.get("/{lid}", response_model=LandmarkOut)
async def detail(lid: str) -> dict:
    return await get_landmark(lid)


@router.patch("/{lid}", response_model=LandmarkOut)
async def update(
    lid: str, payload: LandmarkUpdateIn, user: dict = Depends(get_current_user)
) -> dict:
    fields = payload.model_dump(exclude_none=True)
    return await update_landmark(lid, user["id"], user["role"], fields)


@router.delete("/{lid}", status_code=204)
async def delete(lid: str, user: dict = Depends(get_current_user)) -> None:
    await delete_landmark(lid, user["id"], user["role"])
