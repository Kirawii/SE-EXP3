# 前端

Vue 3 + TypeScript + Vite + Element Plus + Leaflet + Pinia + Vue Router。

## 启动

```bash
cd frontend
npm install            # 首次安装,如默认 cache 不可写加 --cache=/tmp/npm-cache-xtk
npm run dev            # http://localhost:5173
```

开发态 `/api` 已通过 Vite 代理转发到 `http://127.0.0.1:8001`,需要先在 `backend/` 启动 `python3 -m uvicorn app.main:create_app --factory --port 8001` 并保证 Redis 7.2 可达(系统已占用 8000 端口,故选 8001)。

## 脚本

| 命令                | 用途                                    |
| ------------------- | --------------------------------------- |
| `npm run dev`       | 启动 Vite 开发服务器                    |
| `npm run build`     | `vue-tsc` 类型检查 + 生产构建到 `dist/` |
| `npm run preview`   | 本地预览生产构建                        |
| `npm run type-check`| 仅做类型检查                            |

## 目录

```
frontend/src/
├── api/          # 后端接口封装(auth / landmarks / geo)
├── components/   # AppHeader、LandmarkForm
├── router/       # Vue Router 配置 + 鉴权守卫
├── stores/       # Pinia(auth,持久化到 localStorage)
├── styles/       # 全局样式
├── types/        # 后端响应 TS 类型
└── views/        # 5 个核心页面:Map / List / Detail / Login / Register
```

## 页面与路由

| 路径               | 页面     | 说明                                                        |
| ------------------ | -------- | ----------------------------------------------------------- |
| `/map`             | 地图     | 默认页,天地图底图;圆形(BYRADIUS)/矩形(BYBOX)查询、测距(GEODIST)、驾车路径规划、附近商家推荐;城市快选 / 定位 |
| `/explore`         | 探索     | 公开;按名称关键字 + 类别检索已审核地标                     |
| `/landmarks`       | 我的地标 | 需登录                                                      |
| `/landmarks/:id`   | 地标详情 | 地图预览 + 收藏 + 评论;Owner/管理员可编辑、删除           |
| `/favorites`       | 我的收藏 | 需登录                                                      |
| `/profile`         | 个人资料 | 需登录;编辑昵称 / 头像                                     |
| `/admin`           | 管理后台 | 仅管理员;地标审核、用户禁用/启用、导出 CSV                 |
| `/login`           | 登录     | 已登录会重定向到 `/map`                                      |
| `/register`        | 注册     | 注册成功后自动登录并跳 `/map`;首个注册用户为管理员        |

## 备注

- 瓦片来源 OSM (`https://{s}.tile.openstreetmap.org/...`),如需切换替换 `MapView.vue` 与 `LandmarkDetailView.vue` 中的 tileLayer 即可。
- Leaflet 默认 marker 图标走 unpkg CDN,离线演示前请提前预热或改本地路径。
- 主 bundle 包含 Element Plus 全量,后续如需精简可引入 `unplugin-vue-components` 做按需注册。
