from typing import Annotated

from fastapi import APIRouter, Query

from ..config import get_settings
from ..errors import NotFound
from ..landmarks.repository import hydrate_many
from ..redis_client import K, redis
from .schemas import CoordinateOut, DistanceOut, GeohashOut, NearbyHit, RecommendHit


router = APIRouter()


def _build_hits(raw: list, fallback: dict[str, dict]) -> list[NearbyHit]:
    """raw 形如 [(name, dist, (lng, lat)), ...]，fallback 是地标实体表。"""
    hits: list[NearbyHit] = []
    for item in raw:
        lid = item[0]
        dist = float(item[1])
        coord = item[2]
        lng, lat = float(coord[0]), float(coord[1])
        lm = fallback.get(lid)
        if not lm:
            continue
        hits.append(
            NearbyHit(
                id=lid,
                name=lm["name"],
                category=lm["category"],
                lng=lng,
                lat=lat,
                distance_km=round(dist, 3),
            )
        )
    return hits


@router.get("/nearby", response_model=list[NearbyHit])
async def nearby(
    lng: Annotated[float, Query(ge=-180, le=180)],
    lat: Annotated[float, Query(ge=-85.05, le=85.05)],
    radius_km: Annotated[float, Query(gt=0, le=50)] = 5.0,
    limit: Annotated[int, Query(gt=0, le=500)] = 50,
) -> list[NearbyHit]:
    settings = get_settings()
    raw = await redis().geosearch(
        settings.default_geo_key,
        longitude=lng,
        latitude=lat,
        radius=radius_km,
        unit="km",
        sort="ASC",
        count=limit,
        withcoord=True,
        withdist=True,
    )
    if not raw:
        return []
    ids = [item[0] for item in raw]
    by_id = {lm["id"]: lm for lm in await hydrate_many(ids)}
    return _build_hits(raw, by_id)


@router.get("/box", response_model=list[NearbyHit])
async def box(
    lng: Annotated[float, Query(ge=-180, le=180)],
    lat: Annotated[float, Query(ge=-85.05, le=85.05)],
    width_km: Annotated[float, Query(gt=0, le=200)],
    height_km: Annotated[float, Query(gt=0, le=200)],
    limit: Annotated[int, Query(gt=0, le=500)] = 100,
) -> list[NearbyHit]:
    settings = get_settings()
    raw = await redis().geosearch(
        settings.default_geo_key,
        longitude=lng,
        latitude=lat,
        width=width_km,
        height=height_km,
        unit="km",
        sort="ASC",
        count=limit,
        withcoord=True,
        withdist=True,
    )
    if not raw:
        return []
    ids = [item[0] for item in raw]
    by_id = {lm["id"]: lm for lm in await hydrate_many(ids)}
    return _build_hits(raw, by_id)


@router.get("/recommend", response_model=list[RecommendHit])
async def recommend(
    lng: Annotated[float, Query(ge=-180, le=180)],
    lat: Annotated[float, Query(ge=-85.05, le=85.05)],
    radius_km: Annotated[float, Query(gt=0, le=50)] = 5.0,
    category: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(gt=0, le=50)] = 10,
) -> list[RecommendHit]:
    """附近商家推荐：GEOSEARCH 取附近地标，按「距离 + 热度(收藏数)」加权排序。"""
    settings = get_settings()
    raw = await redis().geosearch(
        settings.default_geo_key,
        longitude=lng,
        latitude=lat,
        radius=radius_km,
        unit="km",
        sort="ASC",
        count=200,
        withcoord=True,
        withdist=True,
    )
    if not raw:
        return []

    ids = [item[0] for item in raw]
    by_id = {lm["id"]: lm for lm in await hydrate_many(ids)}

    # 取每个候选的收藏数作为热度
    pipe = redis().pipeline()
    for lid in ids:
        pipe.scard(K.fav_by_landmark(lid))
    pops = await pipe.execute()
    pop_by_id = dict(zip(ids, (int(p) for p in pops)))
    max_pop = max(pop_by_id.values()) if pop_by_id else 0

    scored: list[RecommendHit] = []
    for item in raw:
        lid = item[0]
        lm = by_id.get(lid)
        if not lm:
            continue
        if category and lm["category"] != category:
            continue
        dist = float(item[1])
        lng_v, lat_v = float(item[2][0]), float(item[2][1])
        pop = pop_by_id.get(lid, 0)
        proximity = 1 - min(dist / radius_km, 1.0)
        popularity_norm = pop / max_pop if max_pop else 0.0
        score = round(0.6 * proximity + 0.4 * popularity_norm, 4)
        scored.append(
            RecommendHit(
                id=lid,
                name=lm["name"],
                category=lm["category"],
                lng=lng_v,
                lat=lat_v,
                distance_km=round(dist, 3),
                popularity=pop,
                score=score,
            )
        )

    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:limit]


@router.get("/distance", response_model=DistanceOut)
async def distance(a: str, b: str) -> DistanceOut:
    settings = get_settings()
    d = await redis().geodist(settings.default_geo_key, a, b, unit="km")
    if d is None:
        raise NotFound("两个地标至少有一个未注册到 GEO")
    return DistanceOut(a_id=a, b_id=b, distance_km=round(float(d), 3))


@router.get("/geohash/{lid}", response_model=GeohashOut)
async def geohash(lid: str) -> GeohashOut:
    settings = get_settings()
    res = await redis().geohash(settings.default_geo_key, lid)
    if not res or res[0] is None:
        raise NotFound("地标未注册到 GEO")
    return GeohashOut(id=lid, geohash=res[0])


@router.get("/position/{lid}", response_model=CoordinateOut)
async def position(lid: str) -> CoordinateOut:
    settings = get_settings()
    res = await redis().geopos(settings.default_geo_key, lid)
    if not res or res[0] is None:
        raise NotFound("地标未注册到 GEO")
    lng, lat = res[0]
    return CoordinateOut(id=lid, lng=float(lng), lat=float(lat))
