# 习惯打卡（Habit Check-in）

Uniapp Vue3（H5）+ FastAPI（异步）+ MySQL 8 + Redis 的习惯打卡应用。重点不在功能数量，而在三件事做对：**连续天数算法、并发零重复、接口与缓存的一致性**。

已通过的真实验证：18 个单元测试、10 步全链路冒烟、20 并发打卡（1 成功 / 19 冲突 / 数据库仅 1 条）、浏览器端到端流程（登录→建项→打卡→刷新持久化→退出）。证据见 [docs/验收证据.md](docs/验收证据.md) 与 [docs/验收日志.txt](docs/验收日志.txt)。

## 功能

- 登录 / 退出：Redis 不透明 token 会话，7 天 TTL，退出立即失效
- 创建打卡项：同一用户下名称唯一，重复创建返回 400
- 每日打卡：同一用户同一天只会产生一条记录（三层防重）
- 连续天数：逐天校验，覆盖断签、跨月、跨年、闰年、重复打卡
- H5 页面：登录、首页打卡列表、新建打卡项

## 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Uniapp + Vue3 组合式 API + Vite，仅编译 H5 |
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy 2.x（异步）/ Pydantic v2 |
| 数据库 | MySQL 8.0（3 张表 + 联合唯一索引） |
| 缓存 | Redis 6+（4 类 key，见下表） |
| 时区 | 服务端统一 `ZoneInfo("Asia/Shanghai")` |
| 环境 | `pydantic-settings` + `.env`，Compose 一键起中间件 |

## 目录结构

```
habit-checkin/
├── docker-compose.yml        # MySQL 8.0 + Redis 7
├── .env.example              # Compose 环境变量模板
├── backend/
│   ├── app/
│   │   ├── main.py           # CORS、请求日志、全局异常、路由装配
│   │   ├── api/              # auth.py / item.py / check.py
│   │   ├── service/          # 业务逻辑
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 入参
│   │   ├── common/           # 统一返回、错误码、鉴权依赖、时间工具、Redis key
│   │   └── db/               # MySQL / Redis 客户端
│   ├── tests/                # 连续天数 + 时区单元测试
│   ├── scripts/              # smoke.py / concurrency_check.py / gen_hash.py
│   ├── init.sql              # 建库建表、索引、演示账号
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/pages/            # login / index / add 三个页面
│   ├── src/api/request.js    # token 注入、401 拦截、统一错误提示
│   ├── src/env.js            # 后端地址
│   ├── package.json
│   └── vite.config.js
└── docs/                     # 验收证据、日志、截图
```
##
[View Demo video](【2026-10-20 22-43-20】https://www.bilibili.com/video/BV1LcnK6bEcg?vd_source=66902c9bf26a37c7ac46b23c9a45ddd1)
## 5 分钟启动

### 1. 准备

Docker Desktop（含 Compose）、Python 3.10+、Node 18+。

### 2. 复制并修改环境变量

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

两个文件里的数据库密码保持一致；`DB_HOST=127.0.0.1`、`DB_PORT=3306`、`REDIS_PORT=6379` 为 Docker 默认映射。

### 3. 启动 MySQL 与 Redis

```bash
docker compose up -d
docker compose ps        # 等两个服务 healthy
#有可能会出现端口占用backend.\env内默认端口号3306改为3307 docker-compose.yml内的ports：-"3307:3306"即可 
#如果正常不用理会上面这条

```

首次启动会自动执行 `backend/init.sql` 并创建演示账号 `demo / 123456`。重置数据：`docker compose down -v && docker compose up -d`。

### 4. 启动后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动后接口文档：<http://127.0.0.1:8000/docs>。

> Windows 无需额外安装时区库：`tzdata` 已在依赖里。`bcrypt` 必须保持 4.0.1（passlib 1.7.4 与 4.1+ 不兼容）。

### 5. 启动前端

```bash
cd frontend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
npm install
npm run dev:h5
```

打开 <http://localhost:5173>，使用 `demo / 123456` 登录。npm 慢时可先执行：

```bash
npm config set registry https://registry.npmmirror.com
```

### 6. 验证（后端运行中）

```bash
cd backend
python -m pytest -q                 # 18 passed
python scripts/smoke.py             # 六接口全链路，10 步
python scripts/concurrency_check.py # 20 并发：1 成功 / 19 冲突 / DB 1 条
```

## 接口一览

统一返回结构（所有接口）：

```json
{"code": 200, "msg": "success", "data": {}}
```

HTTP 状态码与 `code` 一致；除登录外都需要 `Authorization: Bearer {token}`。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/login` | 登录，返回 token 与用户信息 |
| POST | `/api/auth/logout` | 退出登录，服务端删除 token |
| GET | `/api/items` | 打卡项列表（含今日状态、连续天数、server_date） |
| POST | `/api/items` | 创建打卡项（同名返回 400） |
| POST | `/api/check/{item_id}` | 今日打卡（重复/并发返回 409） |
| GET | `/api/check/streak/{item_id}` | 查询连续天数与今日状态 |

错误码：`200` 成功、`400` 参数/凭证/资源错误、`401` 未登录或 token 失效、`409` 今日已打卡（含锁冲突）、`500` 服务器内部错误。

## Redis 设计（4 类 key）

| Key | Value / TTL | 为什么放 Redis | 一致性策略 |
|---|---|---|---|
| `login:token:{token}` | user_id / 7 天 | 每个请求都鉴权，高频读，不该压 MySQL | 登录 SET，登出 DEL，过期自动清理 |
| `check:today:{item_id}:{YYYYMMDD}` | `"1"` / 到北京零点 | 首页每次都要查 N 个打卡项的今日状态，MGET 一次取回 | 事务提交成功后 SET；读未命中回源查库并回填 |
| `streak:{item_id}` | `{"streak":n,"as_of":"YYYY-MM-DD"}` / 24 小时 | 连续天数要遍历历史，计算昂贵 | 打卡前 DEL，读回填；`as_of` 不是今天就强制回源（防零点后旧值） |
| `lock:check:{item_id}:{YYYYMMDD}` | 随机 uuid / 10 秒 | 多 worker / 多实例互斥，前置保护数据库 | `SET NX PX` 加锁，Lua 比对 uuid 后释放 |

## 核心设计

**连续天数（逐天校验）**：一条 SQL 取回全部 `check_date`，从今天（今天没打则从昨天）开始逐日回退，遇到缺口立即停止。禁止 `(today - last).days + 1` 这类日期差公式——它会把「断签 3 天」算成连续 4 天。数据库中 `current_streak` 是存储口径（截至最后一次打卡），接口返回的是按今天重算的展示口径，回源时懒修复库值。

**并发三层防护**：

1. `check:today` 缓存快路径：挡住重复点击；
2. Redis 锁：同一 item + 同一天只允许一个请求进入事务；
3. MySQL `uk_item_date(item_id, check_date)`：物理兜底，冲突时回滚并返回 409。

**缓存一致性**：写路径先失效缓存再写库；读路径先读缓存、未命中回源、回填。`check:today` 属于「提交后写标记」，`streak` 属于标准 Cache Aside，两者策略分开。

## 验证结果（2026-10-20 实测）

| 项目 | 结果 |
|---|---|
| 单元测试 | `18 passed`（连续天数 12 用例 + 时区 6 用例） |
| 冒烟 | 6 接口 10 步全通过，含 409 与 401 分支 |
| 并发 | 20 并发：`success=1 conflict=19 db_record_count=1` |
| Redis | 登录 TTL 604800；当日标记 TTL 到零点；streak 缓存带 `as_of` |
| 数据库兜底 | 重复插入报 `Duplicate entry ... uk_item_date`（1062） |
| H5 | `uni build` 成功；Playwright 真实浏览器跑通登录→建项→打卡→刷新→退出，无控制台错误 |

截图在 `docs/screenshots/`。完整原始日志见 [docs/验收日志.txt](docs/验收日志.txt)。

## 常见问题

- **端口冲突**：修改 `docker-compose.yml` 的映射端口，并同步 `backend/.env` 的 `DB_PORT` / `REDIS_PORT`。
- **前端换后端地址 / 局域网演示**：改 `frontend/src/env.js` 的 `BASE_URL`，同时把来源加入 `backend/.env` 的 `CORS_ORIGINS`。
- **初始化脚本没执行**：只在数据卷为空时执行；用 `docker compose down -v` 重置后再启动。
- **Windows 时区报错**：确认 `tzdata` 已安装（requirements 已包含）。
- **bcrypt 报 `__about__`**：bcrypt 版本被升级了，锁回 `4.0.1`。

## 已知取舍

- 按需求只提供登录，没有注册接口；演示账号由 `init.sql` 预置。
- 未做登录失败限流，生产环境建议按 IP + 用户名加计数。
- Cache Aside 存在极小竞态窗口（删除后、回填前读回旧值），当前用 `as_of` + 懒修复兜底；更高要求可加延迟双删或版本号。
- 集成测试依赖真实 MySQL/Redis，未接入 CI；迁移时可用 Testcontainers 演进。

## Git 历史

仓库按功能阶段提交（初始化 → 建表 → 基础设施 → 认证 → 打卡项 → 打卡/连续天数 → 测试 → 前端 → 文档），可用 `git log --oneline` 查看完整演进。
