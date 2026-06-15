from pydantic import BaseModel, Field


class NearbyHit(BaseModel):
    id: str
    name: str
    category: str
    lng: float
    lat: float
    distance_km: float


class RecommendHit(BaseModel):
    id: str
    name: str
    category: str
    lng: float
    lat: float
    distance_km: float
    popularity: int  # 收藏数
    score: float  # 距离 + 热度 加权得分


class DistanceOut(BaseModel):
    a_id: str
    b_id: str
    distance_km: float


class GeohashOut(BaseModel):
    id: str
    geohash: str


class CoordinateOut(BaseModel):
    id: str
    lng: float
    lat: float
