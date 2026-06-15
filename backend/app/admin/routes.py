import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from ..deps import require_role
from ..landmarks.repository import list_by_status, update_landmark
from ..landmarks.schemas import LandmarkOut
from ..users.repository import list_all_users, set_disabled
from ..users.routes import to_public
from ..users.schemas import UserPublicOut
from .schemas import ReviewIn


# 整个路由组要求 ADMIN 角色
router = APIRouter(dependencies=[Depends(require_role("ADMIN"))])


@router.get("/landmarks", response_model=list[LandmarkOut])
async def admin_list_landmarks(
    status: Annotated[str, Query(pattern="^(PENDING|APPROVED|REJECTED)$")] = "PENDING",
) -> list[dict]:
    return await list_by_status(status)


@router.post("/landmarks/{lid}/review", response_model=LandmarkOut)
async def admin_review(
    lid: str, payload: ReviewIn, admin: dict = Depends(require_role("ADMIN"))
) -> dict:
    new_status = "APPROVED" if payload.action == "approve" else "REJECTED"
    return await update_landmark(lid, admin["id"], "ADMIN", {"status": new_status})


@router.get("/users", response_model=list[UserPublicOut])
async def admin_list_users() -> list[UserPublicOut]:
    return [to_public(u) for u in await list_all_users()]


@router.post("/users/{uid}/disable", response_model=UserPublicOut)
async def admin_disable_user(uid: str) -> UserPublicOut:
    return to_public(await set_disabled(uid, True))


@router.post("/users/{uid}/enable", response_model=UserPublicOut)
async def admin_enable_user(uid: str) -> UserPublicOut:
    return to_public(await set_disabled(uid, False))


@router.get("/export/landmarks.csv")
async def admin_export_landmarks() -> StreamingResponse:
    rows: list[dict] = []
    for status in ("APPROVED", "PENDING", "REJECTED"):
        rows.extend(await list_by_status(status))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["id", "name", "category", "status", "lng", "lat", "owner_id", "created_at"]
    )
    for r in rows:
        writer.writerow(
            [r["id"], r["name"], r["category"], r["status"], r["lng"], r["lat"], r["owner_id"], r["created_at"]]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=landmarks.csv"},
    )
