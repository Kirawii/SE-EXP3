from typing import Literal

from pydantic import BaseModel, Field


LandmarkStatus = Literal["PENDING", "APPROVED", "REJECTED"]


class LandmarkCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    category: str = Field(..., min_length=1, max_length=30)
    description: str = Field(default="", max_length=500)
    image_url: str | None = Field(default=None, max_length=300)
    lng: float = Field(..., ge=-180, le=180)
    lat: float = Field(..., ge=-85.05, le=85.05)


class LandmarkUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    category: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=300)
    lng: float | None = Field(default=None, ge=-180, le=180)
    lat: float | None = Field(default=None, ge=-85.05, le=85.05)
    status: LandmarkStatus | None = None


class LandmarkOut(BaseModel):
    id: str
    name: str
    category: str
    description: str = ""
    image_url: str | None = None
    owner_id: str
    status: LandmarkStatus
    lng: float
    lat: float
    created_at: str
    updated_at: str = ""
