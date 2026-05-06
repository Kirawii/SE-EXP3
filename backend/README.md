# 地标管理 · 后端

FastAPI + redis-py（asyncio）+ PyJWT。所有数据存于 Redis：地标实体落 Hash，坐标落 GEO 有序集合，索引落 Set，限流与吊销落带 TTL 的 String。

## 快速启动

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 启动本地 Redis（任选其一）
redis-server &
# 或：docker run -d --name redis-dev -p 6379:6379 redis:7.2-alpine

uvicorn app.main:app --reload
```

启动后访问：

- API 根路径 <http://localhost:8000>
- Swagger UI <http://localhost:8000/docs>
- ReDoc <http://localhost:8000/redoc>
- 健康检查 <http://localhost:8000/health>

## 模块

```
app/
├── main.py            # FastAPI 入口、生命周期、异常注册
├── config.py          # 环境变量与默认值
├── redis_client.py    # Redis 连接与 Key 命名空间
├── security.py        # JWT 与密码哈希
├── deps.py            # FastAPI 依赖（鉴权、限流、当前用户）
├── errors.py          # 领域异常与统一处理
├── auth/              # 注册 / 登录 / 登出 / Token
├── users/             # 用户资料
├── landmarks/         # 地标 CRUD
└── geo/               # 近邻 / 距离 / 矩形 / Geohash
```

## Redis Key 约定

| 类别 | Key | 类型 | 说明 |
|------|-----|------|------|
| 自增 | `seq:users` `seq:landmarks` | String | INCR 取下一个 ID |
| 用户 | `users:{id}` | Hash | 用户实体 |
| 用户索引 | `users:by_username:{name}` `users:by_email:{email}` | String | 唯一索引 → user_id |
| 角色 | `users:role:{ROLE}` | Set | 角色到 user_id 的反向索引 |
| 鉴权 | `auth:revoked:{jti}` | String + TTL | Token 黑名单 |
| 限流 | `ratelimit:login:{ip}` | String + TTL | 登录次数 |
| 地标 | `landmarks:{id}` | Hash | 地标实体 |
| 地标索引 | `landmarks:by_owner:{uid}` `landmarks:by_status:{s}` `landmarks:by_category:{c}` | Set | 反向索引 |
| 地理坐标 | `geo:landmarks` | Sorted Set (GEO) | GEOADD/GEOSEARCH 目标 |

## 测试

```bash
pip install -r requirements-dev.txt
# 测试默认使用 db 15，避免污染开发数据
pytest
```
