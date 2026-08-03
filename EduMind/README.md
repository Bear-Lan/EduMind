# EduMind V1.0 — AI 驱动的自适应个性化协同学习平台

> **版本号**：V1.0 (Release)  
> **使用对象**：测试人员 / 同学 / 开发者  
> **适用平台**：Windows / macOS / Linux  

---

## 📖 1. 项目简介

**EduMind** 是一套专为 **全学段（小学、初中、高中、大学/职业）** 学生打造的 AI 驱动自适应学习系统。系统通过**知识图谱拓扑**、**检索增强生成 (RAG)** 以及 **启发式自适应推荐引擎**，根据每位学生的年级与掌握情况，自动推荐最佳的突破章节、生成三步学习任务卡，并提供 AI 智能导师实时协同答疑。

### 🌟 核心特性
- 🎓 **全学段体系自适应**：原生适配小学、初中、高中、大学四大阶段，涵盖数学、英语、物理、化学、计算机等核心学科。
- 🎯 **自适应推荐闭环**：基于知识拓扑前置依赖，打卡测验后自动解锁推演下一阶段突破章节，永不断流。
- 💬 **AI 教练 + RAG 知识库**：整合 Qdrant 本地向量数据库，提问时自动检索教辅资料，提供精准启发的解题辅导。
- 📊 **四维可视化仪表盘**：整合雷达图、学习时长抛物线、耗时饼图与里程碑 Timeline。
- ⚡ **离在线双模支持**：未配置 API Key 时自动启用结构化离线拟真模式；录入 Key 后无缝升级为 DeepSeek 全量智能大脑。

---

## 🚀 2. 快速上手与操作指南

### 2.1 环境要求
- **Python**：3.10 / 3.11 / 3.12（**推荐 3.11**；**3.14 不支持**——pydantic-core 0.27 系列没有 cp314 预编译 wheel，编译会失败）
- **Node.js**：v18+ (包含 npm)
- **Git**：任意

### 2.2 一键启动（推荐）
直接双击项目根目录下的批处理脚本：
```bash
start_edumind.bat
```
脚本会自动检查依赖环境，同时拉起 **FastAPI 后端服务 (`http://127.0.0.1:8000`)** 与 **Vite 前端服务 (`http://localhost:5173`)**，并自动在浏览器中打开主界面。

### 2.3 演示账号登录
打开页面后，直接输入预置的演示账号登录体验：
- **用户名**：`demo_student`
- **密 码**：`DemoPassword123!`

*(亦可点击“注册账号”，创建全新的个人学生档案)*

---


### 2.4 协作者从零开始（克隆后 5 分钟跑通）

如果你刚刚 `git clone` 了本仓库，需要先把缺失的本地数据补齐：

```bash
# 1) 克隆
git clone https://github.com/Bear-Lan/EduMind.git
cd EduMind/EduMind

# 2) 后端 venv + 依赖
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt

# 3) 前端依赖
cd frontend && npm install && cd ..

# 4) 准备 .env（保持空白也能跑，但 RAG 失效）
copy .env.example .env
# 推荐：申请硅基流动免费 key 填到 EMBEDDING_API_KEY（5 分钟，免费档 5000 万 token）
# https://siliconflow.cn 注册 → 实名 → 创建 API Key

# 5) 灌演示数据 + 教辅知识库（数据库和向量库不在仓库里）
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
# 看到 "EduMind V1 ready" 后 Ctrl+C 停掉
.\venv\Scripts\python.exe scripts\seed_demo_student.py
.\venv\Scripts\python.exe scripts\seed_resources_v2.py
# ↑ 这一步必须在**后端停掉**时跑（Qdrant 文件锁）

# 6) 启动
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend
# 另开终端：cd frontend && npm run dev
```

> 详细排错（SmartScreen / 401 / 维度冲突 / 中文乱码）见 **CONTRIBUTING.md**。

### 2.5 协作者速查表

| 想做什么 | 跑什么 |
|---|---|
| 启动后端 | `venv\Scripts\python.exe -m uvicorn main:app --app-dir backend` |
| 启动前端 | `cd frontend && npm run dev` |
| 重置 demo 数据 | `del data\edumind.db` + `python scripts\seed_demo_student.py` |
| 重新入库教辅 | `python scripts\seed_resources_v2.py`（先停后端） |
| 重置向量库 | `rm -rf data\qdrant_storage` + 重跑 seed |
| 健康检查 | `curl http://127.0.0.1:8000/api/v1/health` |

为什么数据库和向量库不在仓库里？见 **CONTRIBUTING.md** 第 2 节。

---### 2.6 功能操作测试流程（建议测试同学按此顺序体验）

```
[1. 切换学段/学科] ➔ [2. 学习计划三步打卡] ➔ [3. AI 教练互动答疑] ➔ [4. 知识测评中心] ➔ [5. 数据分析与图表]
```

#### 步骤 1：学段与学科切换
- 点击顶部导航栏左侧的下拉菜单，尝试选择 `高中 数学`、`初中 英语`、`小学 数学` 或 `计算机科学`。
- **观察点**：左侧“知识画像”大纲会即时更新为符合该学段难度的 4~10 个知识章节拓扑。

#### 步骤 2：学习计划三步打卡
- 在中间“学习计划”面板中，点击 Step 01 右侧的 **“标记完成 ✓”**。
- **观察点**：Step 01 标记为已完成，Step 02 自动解锁。按提示完成 Step 02，解锁 Step 03【开始测验】。

#### 步骤 3：AI 智能教练互动
- 在右侧“AI 教练”对话框中输入你的疑问（如：*“教练，请问一元二次方程求根公式怎么推导？”*）。
- **观察点**：AI 教练会以启发式引导的方式进行知识点剖析，并给出步骤建议。

#### 步骤 4：知识测评中心
- 点击顶部导航栏的 **“📝 测评中心”** 标签页，点击任意知识点卡片发起测验并提交成绩。
- **观察点**：卡片根据得分高低显示不同的颜色光圈（绿色=已掌握，黄色=巩固中，红色=待加强）。

#### 步骤 5：学习进度与数据分析
- 点击顶部 **“📈 学习进度”** 与 **“📊 数据分析”** 标签页。
- **观察点**：查看掌握度雷达图、近 7 天学习时长趋势折线图以及学习里程碑。

---

## 🏛️ 3. 系统程序架构设计

EduMind 采用高度解耦的**前后端分离**架构，后端内部设计遵循微服务分层模式（Layered Microservices Architecture）。

### 3.1 系统整体架构图

```
                         ┌────────────────────────────────────────┐
                         │       前端 Web 界面 (Vue 3 / Vite)      │
                         └───────────────────┬────────────────────┘
                                             │ HTTP REST API (JWT)
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           后端 FastAPI 服务框架                                 │
│                                                                                 │
│  ┌───────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐  │
│  │   API 路由入口    │ ──► │  流程编排器 (Orch)  │ ──► │ 学生画像 (Profile)   │  │
│  │  (api/v1/...)     │     │ (orchestrator.py)   │     │ (service.py)        │  │
│  └───────────────────┘     └──────────┬──────────┘     └─────────────────────┘  │
│                                       │                                         │
│                ┌──────────────────────┼──────────────────────┐                  │
│                ▼                      ▼                      ▼                  │
│      ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐        │
│      │  自适应推荐引擎   │  │   RAG 检索增强    │  │   LLM 模型服务    │        │
│      │(recommendation)   │  │   (rag/service)   │  │   (llm/service)   │        │
│      └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘        │
└────────┼───────┼──────────────────────┼──────────────────────┼──────────────────┘
         │       │                      │                      │
         ▼       ▼                      ▼                      ▼
    ┌─────────────────┐        ┌─────────────────┐    ┌─────────────────┐
    │ SQLite / Postgres│        │ Qdrant 向量数据库│    │ DeepSeek API    │
    │  (系统关系数据)  │        │ (教辅知识向量)  │    │  (在线大模型)   │
    └─────────────────┘        └─────────────────┘    └─────────────────┘
```

---

### 3.2 后端核心模块说明

| 模块名称 | 目录路径 | 核心职责 |
| :--- | :--- | :--- |
| **API 路由层** | `backend/api/` | 负责处理 HTTP 请求校验、JWT 身份认证、统一 JSON 响应格式输出 (`StandardResponse`)。 |
| **应用编排器** | `backend/application/orchestrator.py` | 系统的中央大脑，协调 Profile、Recommendation、RAG 与 LLM 完成复杂学习流程。 |
| **学生画像服务**| `backend/student_profile/` | 维护学生年级、学科、学习偏好及动态知识掌握度地图 (`mastery_map`)。 |
| **推荐引擎** | `backend/recommendation/` | 计算知识点优先级得分 $P_i$，根据前置依赖拓扑自动推荐最优突破章节。 |
| **RAG 向量检索**| `backend/rag/` | 使用 `qdrant-client` 本地向量检索与词向量 Embeddings，实现教辅上下文挂载。 |
| **LLM 服务** | `backend/llm/` | 提供双模 LLM 支持（网络连通时请求 DeepSeek，未连通时触发离线结构化 fallback）。 |

---

### 3.3 前端核心架构说明

- **技术栈**：Vue 3 (Composition API `script setup`) + Vite + Pinia (状态管理) + Vue Router + Chart.js + Marked.js。
- **设计语言 (Design Aesthetics)**：采用暗黑玻璃拟态 (Dark Glassmorphism) 风格，配以紫蓝渐变高光与响应式三栏布局。

---

## ⚙️ 4. API Key 配置说明（可选）

系统默认运行在**离线智能拟真模式**下，无需配置任何 key 即可完整测试全流程。

如果测试同学想要体验真实的大语言模型回答：
1. 点击主界面右上角的 **“⚙️ 配置”** 按钮。
2. 在弹窗中填入你的 `DEEPSEEK_API_KEY`（例如 `sk-xxxxxxxx`）。
3. 点击“保存配置”，系统将即刻切换至 DeepSeek 在线大模型引擎！

---

## ❓ 5. 常见问题排查 (FAQ)

- **Q: 为什么点击“标记完成”没有反应？**  
  **A**: 请检查后端服务是否在运行。执行 `start_edumind.bat` 可确保前后端同时启动。

- **Q: 数据库文件保存在哪里？**  
  **A**: 关系型 SQLite 数据库保存在 `backend/data/edumind.db`；Qdrant 向量数据保存在 `backend/data/qdrant/`。

- **Q: 如何重新初始化测试数据？**  
  **A**: 在项目根目录下运行 `python scripts/seed_demo_student.py` 即可一键恢复初始 demo 数据。

---
*EduMind Team © 2026 | Powered by Advanced AI Agent Architecture*
