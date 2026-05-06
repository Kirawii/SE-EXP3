from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import router as auth_router
from .config import get_settings
from .errors import DomainError, domain_error_handler
from .geo.routes import router as geo_router
from .landmarks.routes import router as landmarks_router
from .redis_client import close_redis, init_redis, redis
from .users.routes import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_redis()
    yield
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Landmark Manager API",
        version="0.1.0",
        description="基于 Redis GEO 的地标管理原型系统",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(DomainError, domain_error_handler)

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(landmarks_router, prefix="/api/v1/landmarks", tags=["landmarks"])
    app.include_router(geo_router, prefix="/api/v1/geo", tags=["geo"])

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        await redis().ping()
        return {"status": "ok"}

    return app


app = create_app()
