# EduMind 协作者指南

> 你是来接手/复现/部署这个项目的开发者。这份文档写给协作者看的，分成**克隆 → 跑通 → 排错**三步。

---

## 1. 5 分钟跑起来

### 1.1 前置要求

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | **3.10 / 3.11 / 3.12**（推荐 3.11） | 后端 |
| Node.js | v18+（含 npm） | 前端 |
| Git | 任意 | 拉代码 |

> ⚠️ **Python 3.13 也能用**；**3.14 不行**（PyO3 0.23 系列的 fewest wheel 还不完整，pydantic-core 编译会失败）。如果你公司/电脑只有 3.14，请先装一个 3.11 用 venv 隔开。

### 1.2 克隆仓库

```bash
git clone https://github.com/Bear-Lan/EduMind.git
cd EduMind/EduMind
```

### 1.3 后端：一键配环境

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt

# macOS / Linux
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
```

> 🎯 `--only-binary=:all:` 强制走预编译 wheel，避免某些机器编译报错。

### 1.4 前端：装依赖

```bash
cd frontend
npm install
cd ..
```

### 1.5 准备 `.env`

```bash
cp .env.example .env       # macOS/Linux
copy .env.example .env     # Windows
```

`.env` 里**必须配置**的只有 `EMBEDDING_API_KEY`（用于教辅向量化）。

#### 1.5.1 申请硅基流动 key（5 分钟，免费）

1. 打开 https://siliconflow.cn → 注册/登录
2. 实名认证（控制台 → 账户管理 → 实名认证），几分钟通过
3. 控制台 → API Keys → 新建 → 复制 `sk-xxx`
4. 填到 `.env`：
```ini
EMBEDDING_API_KEY=sk-你的key
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSIONS=1024
```

> **可以暂时留空**：留空时 `EMBEDDING_API_KEY=` 下 `embedding_service` 会走 **mock 哈希向量**，但 Qdrant 检索召回率会降到 0（推荐先申请）。

### 1.6 跑种子脚本（必跑，自动建库 + 灌教辅）

后端和数据库是**运行时创建**的，仓库里没存。clone 后必须跑：

```bash
# 1) 启后端（先空跑，让 init_db() 建表；再 Ctrl+C 停掉）
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
# 看到 "EduMind V1 ready" 后 Ctrl+C 停掉

# 2) 灌 demo 账号 + 80+ 教辅（98 条向量，含 79 个知识主题）
.\venv\Scripts\python.exe scripts\seed_demo_student.py
.\venv\Scripts\python.exe scripts\seed_resources_v2.py
```

> **关键**：`seed_resources_v2.py` 必须停掉后端运行，因为它要给 Qdrant 写文件，后端启动时 Qdrant 会持锁。
> **耗时**：约 3~5 分钟（80 次 embedding API 调用，免费档内）。

### 1.7 启动

```bash
# 终端 1：后端
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

打开 http://localhost:5173，用 `demo_student / DemoPassword123!` 登录。

### 1.8 或者用项目脚本（一键）

**Windows**：
```bash
start_edumind.bat
```
会自动起后端 + 前端 + 打开浏览器。

---

## 2. 仓库里**没**存的内容（重要）

下面这些文件**不会**出现在仓库里，clone 后自行准备：

| 文件 | 说明 | 怎么准备 |
|---|---|---|
| `EduMind/.env` | 真实密钥（JWT、硅基流动） | 从 `.env.example` 复制并填 key |
| `EduMind/data/edumind.db` | SQLite 运行时数据库 | 跑 seed 脚本自动创建 |
| `EduMind/data/qdrant_storage/` | 向量库二进制文件 | 跑 `seed_resources_v2.py` 重建 |
| `EduMind/venv/` | Python 虚拟环境 | 自行 `python -m venv venv` |
| `EduMind/frontend/node_modules/` | 前端依赖 | 自行 `npm install` |

### 为什么不上传？

- **`.env`**：含真实密钥/密码，泄露=安全事故
- **数据库文件**：每次启动都重建；含敏感数据；merge 冲突
- **向量库**：二进制文件依赖 embedding 模型版本；可随时重建
- **依赖目录**：体积大（venv 几百 MB，node_modules 几十 MB）；库管 PyPI/npm 管

**入库的信息应该可重现**：

```bash
git clone ...                                # 拿代码
pip install -r requirements.txt              # 拿 Python 依赖
npm install                                  # 拿前端依赖
python scripts/seed_*.py                     # 拿 demo 数据 + 教辅知识库
```

→ **任何协作者都能拿到和你本地完全一样的演示环境**。

---

## 3. 常见坑 & 排错

### 3.1 `ModuleNotFoundError: uvicorn` / `pydantic` / `sqlalchemy`

**原因**：没装依赖 或 用了全局 Python 而不是 venv。

解决：
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# 确认后续所有命令都用 .\venv\Scripts\python.exe，不要用裸 python
```

### 3.2 `greenlet_spawn` / `MissingGreenlet` 错误

**原因**：SQLAlchemy 异步懒加载在 ASGI 上下文里不可用。

**已修复**（在 `api/assessment.py`），但如果自己写新 API 遇到：别在 async 函数里 `for r in rows: r.related_obj` 访问关联对象，**用 JOIN 一次性取**。

### 3.3 `Could not validate credentials` / 401

**原因**：JWT 过期（默认 60 分钟）或 token 丢失。

解决：重新登录。**前端 axios 拦截器会自动跳登录页**。

### 3.4 `ESELECT failed: no such table ...`

**原因**：没跑 seed 脚本，数据库空。

解决：跑 `seed_demo_student.py`，它会调 `init_db()` 自动建表。

### 3.5 Qdrant 维度冲突 `could not broadcast input array from shape (1024,) into shape (384,)`

**原因**：旧 Qdrant 用了 384 维（早期 OpenAI embedding），新配置是 1024 维（硅基流动 bge-m3）。

解决：
```bash
# 停后端后，清空 Qdrant 重新入库
rm -rf data/qdrant_storage    # macOS/Linux
Remove-Item -Recurse data/qdrant_storage   # Windows
python scripts/seed_resources_v2.py
```

### 3.6 `ERROR: Failed to upsert point to Qdrant: Storage folder ... is already accessed by another instance`

**原因**：Qdrant 持文件锁——后端和 seed 脚本同时跑。

解决：**先停后端**，再跑 seed；跑完后再起后端。

### 3.7 前端 HMR 不工作 / 改了 .vue 没生效

**原因**：Vite 缓存。

解决：
```bash
# 删缓存重启
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### 3.8 控制台中文乱码（GBK 编码）

**原因**：Windows PowerShell 默认 GBK 而非 UTF-8。

解决：测试时用 PowerShell 7+，或在脚本里加：
```python
sys.stdout.reconfigure(encoding='utf-8')
```
**数据本身没问题**，只是控制台显示乱码。

### 3.9 `pip install` 编译失败（PyO3/_PyInterpreterState）

**原因**：Python 3.14 还不被 PyO3 完整支持。

解决：装 Python 3.11 / 3.12 重建 venv。**不要用 3.14**。

### 3.10 SmartScreen 拦截 `python.exe` 子进程

**原因**：Windows 11 默认开启"智能应用控制"。

解决：Windows 安全中心 → 应用和浏览器控制 → 智能应用控制 → 关闭。或者在保护历史记录里给 `python.exe` 放行。

---

## 4. 怎么改代码

### 4.1 项目结构

```
EduMind/
├── backend/                  # FastAPI 后端
│   ├── api/                  # 路由层
│   ├── application/          # 编排器
│   ├── student_profile/      # 学生画像
│   ├── recommendation/       # 推荐引擎
│   ├── rag/                  # RAG 检索
│   ├── llm/                  # LLM 服务（双模）
│   ├── services/             # 业务服务（判分、选题）
│   ├── models/               # SQLAlchemy ORM
│   ├── schemas/              # Pydantic 校验
│   ├── database/             # DB 连接
│   ├── config/               # 配置
│   ├── core/                 # 依赖注入
│   └── main.py               # 入口
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── pages/            # 页面
│   │   ├── components/       # 组件
│   │   ├── stores/           # Pinia
│   │   ├── router/           # 路由
│   │   └── utils/            # 工具
│   └── package.json
├── scripts/                  # 种子/工具脚本
├── data/                     # 运行时数据（不入库）
├── docs/                     # 架构文档
├── tests/                    # 测试（部分）
├── requirements.txt
├── .env.example
└── start_edumind.bat
```

### 4.2 改后端

1. 改完后 uvicorn 会自动 reload（`--reload` 默认没开，需要带 `--reload` 启动）
2. 改 SQLAlchemy 模型：如果改了字段，记得删 `edumind.db` 重跑 seed（项目没有用 Alembic migration）
3. 改 API 路由：路径加到 `api/router.py` 注册

### 4.3 改前端

1. Vite HMR 自动刷新
2. 改 styles：变量在 `src/styles/main.css` 统一管理
3. 新增页面：记得在 `src/router/index.js` 注册 + `src/pages/DashboardPage.vue` 加 tab

### 4.4 提交代码

```bash
git status                       # 看改动
git add -A                       # stage
git commit -m "feat: 描述"        # 提交
git push                         # 推到远端
```

提交规范（建议）：
- `feat: 新功能`
- `fix: 修复`
- `refactor: 重构`
- `docs: 文档`
- `chore: 杂项`

---

## 5. 核心配置文件速查

| 文件 | 干什么 |
|---|---|
| `requirements.txt` | Python 依赖 |
| `frontend/package.json` | 前端依赖 + scripts |
| `backend/config/settings.py` | 读取 `os.environ` + `.env` |
| `EduMind/.env` | 真实密钥（不入库） |
| `EduMind/.env.example` | 配置模板（入库） |
| `backend/database/connection.py` | 数据库连接 + `init_db()` |
| `backend/llm/service.py:25` | 预置知识图谱（11 个学科 79 主题） |

---

## 6. 任务分工建议（演示版本）

| 角色 | 任务 |
|---|---|
| 后端开发 | 改 API、新增服务、修 bug |
| 前端开发 | 改页面、新组件、调样式 |
| 算法同学 | 调 RAG 检索 / mastery 算法 |
| 演示同学 | 跑通流程、写演示脚本 |
| 数据同学 | 扩教辅数据 / 扩题库 |

每个人跑自己的测试数据，**互不影响**（数据库本地存）。

---

## 7. 出问题时如何求助

按下面顺序排查：

1. **看日志**：后端终端打印 SQLAlchemy 日志（默认 INFO 级别）
2. **看 frontend 浏览器 console**：F12 → Console
3. **问 AI 助手**：把**完整错误日志**复制粘贴
4. **问开发负责人**：截图 + 错误 + 你的操作步骤

---

## 8. 进阶：跑自定义测试

```bash
# 健康检查
curl http://127.0.0.1:8000/api/v1/health

# 登录拿 token
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_student","password":"DemoPassword123!"}'

# 拿知识图谱
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/v1/knowledge-graph

# 跟 AI 教练对话
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"一元二次方程怎么解？"}'
```

---

*EduMind Team © 2026*
