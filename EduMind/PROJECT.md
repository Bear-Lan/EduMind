# EduMind 项目说明

> **版本**：V1.0  
> **定位**：AI 驱动的自适应个性化学习教练平台  
> **仓库路径**：`EduMind/`（前后端同仓）  
> **更新日期**：2026-08

---

## 1. 一句话介绍

**EduMind** 不是普通答题机器人，而是一位 **AI 学习教练**：持续感知学生掌握度，基于知识拓扑推荐下一步学什么，再用 RAG + LLM 解释怎么学，并在学后更新画像，形成闭环。

核心目标：

> 让每位学生在合适的时间，学习合适的知识。

---

## 2. 产品能力概览

| 能力 | 说明 |
|------|------|
| 全学段自适应 | 小学 / 初中 / 高中 / 大学，覆盖数学、英语、物理、化学、计算机等 |
| 自适应推荐 | 依据前置依赖与掌握度 `mastery_map`，生成三步学习任务卡 |
| AI 教练 + RAG | Qdrant 检索教辅向量，结合学生画像生成启发式答疑 |
| 测评与错题本 | 知识点测验、自动评分、错题归档 |
| 学习可视化 | 雷达图、时长趋势、耗时分布、里程碑 Timeline |
| 管理员控制台 | 模型配置（LLM / Embedding）、连通性测试、学生账户启停与重置 |
| 离在线双模 | 未配置 Key 时走结构化离线拟真；配置后走在线大模型 |

### 角色与入口

| 角色 | 入口 | 主要页面 |
|------|------|----------|
| 学生 | `/` 登录 | 仪表盘、画像、学习计划、AI 教练、测评、进度、错题本、知识地图、账户 |
| 管理员 | `/admin-login` | 模型配置控制台、学生用户管理 |

演示学生账号（种子数据）：`demo_student` / `DemoPassword123!`  
首次管理员账号（见 `.env.example`）：`edumind_admin`（首次登录建议立即改密）

---

## 3. 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3（Composition API）+ Vite + Pinia + Vue Router + Chart.js + Marked / KaTeX |
| 后端 | FastAPI + Uvicorn + Pydantic Settings |
| ORM / 迁移 | SQLAlchemy 2（async）+ Alembic + aiosqlite |
| 关系库 | 默认 SQLite（`./data/edumind.db`），可切 PostgreSQL |
| 向量库 | Qdrant（本地路径模式，默认 `./data/qdrant_bge_m3`） |
| Embedding | OpenAI 兼容接口（推荐硅基流动 `BAAI/bge-m3`，1024 维） |
| LLM | OpenAI 兼容接口（默认可配 DeepSeek / Qwen 等） |
| 鉴权 | JWT（学生 / 管理员分角色） |

---

## 4. 仓库结构

```text
EduMind/
├── backend/                 # FastAPI 后端
│   ├── api/                 # HTTP 路由（auth / plan / chat / admin …）
│   ├── application/         # LearningOrchestrator 编排层
│   ├── student_profile/     # 学生画像
│   ├── recommendation/      # 规则推荐引擎 + 前置依赖
│   ├── rag/                 # 检索增强
│   ├── llm/                 # 大模型服务（含离线 fallback）
│   ├── services/            # Embedding、阅卷、模型配置等
│   ├── models/              # SQLAlchemy ORM
│   ├── schemas/             # 请求/响应 DTO
│   ├── database/            # 连接与 Base
│   ├── alembic/             # 数据库迁移
│   └── main.py              # 应用入口
├── frontend/                # Vue 3 前端
│   └── src/pages/           # 业务页面
├── scripts/                 # 种子数据 / 教辅入库脚本
├── tests/                   # 单元测试 + API 测试
├── docs/                    # 架构蓝图与设计文档
├── data/                    # 本地 DB / 向量库（通常不进仓库）
├── .env.example             # 环境变量模板
├── requirements.txt
├── start_edumind.bat        # Windows 一键启动
├── README.md                # 上手与测试手册
├── CONTRIBUTING.md          # 协作者指南
└── PROJECT.md               # 本文件：项目总览
```

---

## 5. 系统架构

前后端分离；后端为分层模块化架构，**业务协调只允许发生在 Orchestrator**。

```text
                    学生 / 管理员
                          │
                          ▼
              前端 Vue 3 (Vite :5173)
                          │  JWT REST
                          ▼
              FastAPI API 层 (/api/v1)
                          │
                          ▼
              Learning Orchestrator
           （唯一跨模块协调入口）
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   StudentProfile  Recommendation  RAG
                                      │
                                      ▼
                                 LLM Service
                          │
                          ▼
              SQLite/Postgres + Qdrant
```

### 设计原则（摘自架构蓝图）

1. **单一职责**：推荐引擎决定「学什么」，LLM 决定「怎么讲」。
2. **单一事实源**：学生状态以 `StudentProfile`（尤其 `mastery_map`）为准。
3. **决策与生成分离**：LLM 不独立决定学习优先级。
4. **模块可替换**：LLM / 向量库 / 推荐算法可独立升级。

### 核心学习闭环

```text
登录 → 测评 / 画像 → 推荐学习路径 → RAG 检索 → AI 辅导
  → 完成任务 / 测验 → 更新掌握度 → 再推荐 …
```

---

## 6. 后端模块职责

| 模块 | 路径 | 职责 |
|------|------|------|
| API 路由 | `backend/api/` | 校验、鉴权、统一 `StandardResponse`，不含业务决策 |
| Orchestrator | `backend/application/orchestrator.py` | 编排画像 → RAG → LLM → 落库等流程 |
| 学生画像 | `backend/student_profile/` | 年级/学科/偏好、`mastery_map` 读写 |
| 推荐引擎 | `backend/recommendation/` | 前置依赖拓扑、优先级得分、生成 `LearningPlan` |
| RAG | `backend/rag/` | 教辅切分、向量检索、上下文拼装 |
| LLM | `backend/llm/` | 在线调用 / 离线结构化回答 |
| 模型配置 | `backend/services/model_config.py` | 管理员配置加密存储与运行时加载 |
| 数据模型 | `backend/models/` | Student、Profile、Plan、History、Chat、Quiz、Admin 等 |

### 主要 API 前缀（`/api/v1`）

| 前缀 | 功能 |
|------|------|
| `/auth` | 学生注册登录、账户资料、改密 |
| `/profile` | 学习画像读写 |
| `/plan` | 生成 / 获取当前学习计划 |
| `/chat` | AI 教练对话与历史 |
| `/assessment` | 测评、测验提交、错题本、阅卷 |
| `/learning` | 完成学习步骤、进度 |
| `/resources` | 教辅检索与 seed |
| `/knowledge-graph` | 知识拓扑 |
| `/analytics` | 仪表盘数据 |
| `/admin` | 管理员登录、模型配置、测通、改密 |
| `/admin/students` | 学生列表、资料/状态/密码管理 |
| `/health` | 健康检查 |

交互式文档：后端启动后访问 `http://127.0.0.1:8000/docs`。

---

## 7. 前端页面地图

| 路由 | 页面 | 权限 |
|------|------|------|
| `/` | 学生登录 / 注册 | 公开 |
| `/dashboard` | 学习主台（三栏：画像 / 计划 / 教练） | 学生 |
| `/profile` | 画像详情 | 学生 |
| `/account` | 账户设置 | 学生 |
| `/assessment` | 测评中心 | 学生 |
| `/plan` | 学习计划 | 学生 |
| `/chat` | AI 教练 | 学生 |
| `/progress` | 学习进度 | 学生 |
| `/error-book` | 错题本 | 学生 |
| `/knowledge-map` | 知识地图 | 学生 |
| `/admin-login` | 管理员登录 | 公开 |
| `/admin` | 模型配置控制台 | 管理员 |
| `/admin/users` | 学生用户管理 | 管理员 |

状态：`Pinia`（`stores/auth.js`）；请求：`utils/api.js`（Axios + JWT）。

---

## 8. 数据模型（精简）

```text
Student ──1:1── StudentProfile（mastery_map / preferences / last_recommendation）
   ├── LearningPlan
   ├── LearningHistory
   ├── ChatSession ── ChatMessage
   └── QuizAttempt

LearningResource          # 教辅元数据（向量在 Qdrant）
QuizQuestion

AdminUser
SystemModelConfig         # 单行：加密的 LLM / Embedding 配置
```

本地默认数据路径：

- SQLite：`EduMind/data/edumind.db`
- Qdrant：`EduMind/data/qdrant_bge_m3`（以 `.env` 为准）

关系库与向量库一般不进 Git，需用 seed 脚本初始化（见 `CONTRIBUTING.md` / `README.md`）。

---

## 9. 本地运行（速览）

**环境**：Python 3.10–3.12（推荐 3.11；3.14 不支持）、Node.js 18+

```bash
# 一键（Windows）
start_edumind.bat

# 或手动
# 后端
python -m venv venv
.\venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
copy .env.example .env
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000

# 前端（另开终端）
cd frontend && npm install && npm run dev
```

首次完整体验还需（后端停掉后执行向量入库，避免 Qdrant 文件锁）：

```bash
.\venv\Scripts\python.exe scripts\seed_demo_student.py
.\venv\Scripts\python.exe scripts\seed_resources_v2.py
```

- 前端：`http://localhost:5173`
- 后端：`http://127.0.0.1:8000`
- 健康检查：`GET /api/v1/health`

更细的排错与协作说明见 `README.md`、`CONTRIBUTING.md`。

---

## 10. 配置要点

配置来源优先级：管理员控制台写入的 `SystemModelConfig`（加密）+ `.env` 启动默认值。

| 变量 | 作用 |
|------|------|
| `DATABASE_URL` | 空则用 SQLite |
| `QDRANT_PATH` / `QDRANT_COLLECTION_NAME` | 本地向量库 |
| `EMBEDDING_*` | 向量模型（维度须与已有 collection 一致） |
| `DEEPSEEK_*` | LLM（命名历史原因；实际可为任意 OpenAI 兼容服务） |
| `ADMIN_BOOTSTRAP_*` | 库空时引导创建首个管理员 |
| `JWT_SECRET_KEY` | 生产环境必须更换 |

未配置有效 API Key 时，LLM 自动降级为离线结构化回答，主流程仍可演示。

---

## 11. 测试

```text
tests/
├── unit/           # orchestrator / llm / rag / student_profile 等
└── api_tests/      # 端点级测试
```

建议在改动推荐、RAG、鉴权、管理员配置相关逻辑后补跑对应测试。

---

## 12. 设计文档索引

| 文档 | 内容 |
|------|------|
| `docs/00 project overview.md` | 愿景、MVP 范围、设计哲学 |
| `docs/01 Architecture.md` | 分层与模块边界 |
| `docs/03 Data Model.md` | 实体与关系 |
| `docs/04 Module Design.md` | 模块内部设计 |
| `docs/05 Event Flow.md` | 运行时事件流 |
| `docs/06 API Spec.md` | API 规格 |
| `docs/07 Development Roadmap.md` | 开发路线图 |
| `README.md` | 安装、演示、测试操作 |
| `CONTRIBUTING.md` | 克隆、seed、常见问题 |

---

## 13. 当前状态与边界

**V1 已具备**：完整学习闭环、规则推荐、RAG 辅导、测评/错题、可视化、学生账户、管理员模型与用户管理。

**明确不在 V1 核心范围**（架构蓝图）：多智能体、MCP、语音、强化学习、复杂 IRT 自适应测验、重度多模态等。知识图谱前端已有展示入口，深度图计算仍属可演进方向。

---

*EduMind Team · Powered by Orchestrator + RAG + LLM*
