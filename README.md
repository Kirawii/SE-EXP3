# 地标管理原型系统

软件工程课程设计 · 基于 Redis GEO 的地标录入、检索与近邻查询原型。

## 团队

许桐恺(PO)· 闫晨曦(SM / 后端 Lead)· 肖旭仁(后端 / Redis)· 侯躍铖(前端)· 魏振邦(测试 / DevOps)

## 周期

1 周(5 工作日 + 周末缓冲),单 Sprint Scrum 节奏。

## 文档导航

| 文档                                  | 内容                                                            |
| ------------------------------------- | --------------------------------------------------------------- |
| [项目报告](docs/项目报告.md)          | **提交主文档**:团队/工作量、需求、系统设计、用例图与类图、功能演示 |
| [01 项目方案](docs/01-项目方案.md)    | 团队分工、Redis 环境、功能与非功能需求、Scrum 过程管理         |
| [03 用例图](docs/03-用例图.md)        | 参与者、用例分组、关键用例规约、关系说明                        |

图源文件:用例图 [`use-case.puml`](docs/use-case.puml) / [`use-case.mmd`](docs/use-case.mmd);类图 [`class-diagram.puml`](docs/class-diagram.puml) / [`class-diagram.mmd`](docs/class-diagram.mmd)。

## 目录结构

```
SE/
├── README.md
├── docs/
│   ├── 01-项目方案.md
│   ├── 03-用例图.md
│   ├── use-case.puml
│   └── use-case.mmd
├── backend/
│   ├── app/             # FastAPI 应用(routes / repository / schemas / security)
│   ├── tests/           # pytest 冒烟测试
│   ├── requirements.txt
│   └── pytest.ini
└── frontend/
    ├── src/             # Vue 3 + TS 源码(views / components / api / stores)
    ├── package.json
    └── vite.config.ts
```

## 技术栈

后端 FastAPI + redis-py(asyncio)+ PyJWT + passlib · 前端 Vue 3 + Element Plus + Leaflet · 数据 Redis 7.2(同时承担实体与 GEO 索引,无关系数据库)。
