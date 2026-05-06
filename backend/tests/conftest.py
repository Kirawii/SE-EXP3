import os
import sys
from pathlib import Path

# 把 backend/ 加入 import path，便于脚本直接 `pytest` 运行
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 测试默认走 db 15，避免污染开发数据；也用独立 secret
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod-please-ignore-32b")
os.environ.setdefault("LOGIN_RATE_LIMIT", "100")  # 测试不被限流卡住

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.redis_client import close_redis, init_redis, redis


@pytest_asyncio.fixture
async def client():
    application = create_app()
    await init_redis()
    await redis().flushdb()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await redis().flushdb()
    await close_redis()
