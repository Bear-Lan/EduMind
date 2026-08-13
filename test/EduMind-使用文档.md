# EduMind V1.0 部署使用文档

> AI 驱动自适应个性化协同学习平台
> 面向体验测试人员的快速上手指南

---

## 一、环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.10 / 3.11 / 3.12（推荐 3.11） | 后端运行环境，**必须安装** |
| **Node.js** | 不需要 | 前端已预构建，无需 Node.js |
| **操作系统** | Windows 10/11 | 当前部署包仅支持 Windows |

### Python 安装验证

打开命令行，输入：
```
python --version
```
如果显示 `Python 3.10.x` ~ `Python 3.12.x` 即可。如果提示找不到命令，请从 [python.org](https://www.python.org/downloads/) 下载安装，安装时勾选 **Add Python to PATH**。

> **注意**：不支持 Python 3.13/3.14，部分依赖库没有对应版本的预编译包。

---

## 二、快速启动（3 步）

### 步骤 1：解压部署包

将 `EduMind-deploy.zip` 解压到任意目录，例如：
```
D:\EduMind\
├── deploy.bat
├── .env
├── requirements.txt
├── backend\
├── frontend\
│   └── dist\          ← 预构建前端
└── data\              ← 数据库 + 向量库
```

### 步骤 2：双击运行 `deploy.bat`

首次运行时脚本会自动完成以下操作（约 2-3 分钟）：
1. 创建 Python 虚拟环境（`venv\`）
2. 安装后端 Python 依赖（从 `requirements.txt`）
3. 检测到前端已预构建 → 跳过前端构建
4. 启动服务

当看到以下输出时，说明启动成功：
```
[START] Launching EduMind (Port 8000)...

  Web App:    http://localhost:8000
  API Docs:   http://localhost:8000/docs
```

### 步骤 3：打开浏览器

浏览器会自动打开 `http://localhost:8000`，如果没有自动打开，手动访问即可。

---

## 三、登录账号

部署包内置了演示账号，直接登录即可体验：

### 学生账号（主要体验用）

| 用户名 | 密码 |
|--------|------|
| `demo_student` | `DemoPassword123!` |

### 管理员账号（配置 AI 模型用）

| 用户名 | 密码 |
|--------|------|
| `edumind_admin` | `EduMindTeam#2026!` |

> 首次登录管理员后建议立即修改密码。

---

## 四、功能体验指南

建议按以下顺序体验核心功能：

### 4.1 学习主控台（首页）

登录后默认进入主控台，三栏布局：
- **左栏 - 学习画像**：显示当前学科各章节掌握度
- **中栏 - 学习计划**：三步任务卡（顺序解锁）+ 概念技能树（Markmap 可视化）
- **右栏 - AI 教练**：对话式答疑

### 4.2 AI 教练对话 + 苏格拉底引导

1. 在右栏 AI 教练对话框输入问题，例如：`请讲一下勾股定理`
2. AI 会基于教辅资料回答（附引用卡片，可展开查看原文）
3. **开启苏格拉底模式**：输入框上方有「🧠 苏格拉底引导」开关
   - 开启后，AI 不会直接给答案，而是用提问引导你自己推理
   - 适合用来做探究式学习

### 4.3 Magic Notes — 笔记一键变刷题集

1. 点击顶部导航栏的 **「✨ Magic Notes」** 标签
2. 在文本框中粘贴一段课堂笔记或学习材料（至少 20 字）
3. 点击 **「🪄 生成刷题集」**
4. AI 自动生成 5-8 道结构化题目（单选/判断/填空/简答混合）
5. 点击 **「✏️ 开始练习」** 逐题作答，自动批改并显示得分

### 4.4 学习计划与概念技能树

1. 在中栏点击 Step 01 的「标记完成 ✓」
2. Step 02 自动解锁，依次完成三步
3. 概念技能树（Markmap 图）展示章节知识点掌握度：
   - 灰色 = 未开始（L0）
   - 浅绿 = 了解（L1）
   - 绿色 = 熟练（L2）
   - 深绿 = 精通（L3）
4. 点击叶子节点末尾的圆点，可打开「知识点精讲」和「例题练习」

### 4.5 测评中心

1. 点击顶部 **「📝 测评中心」** 标签
2. 点击任意知识点卡片发起测验
3. 提交后根据得分显示不同颜色（绿色=掌握，黄色=巩固，红色=待加强）

### 4.6 其他功能

| 标签 | 功能 |
|------|------|
| 📕 错题本 | 查看历次做错的题目 |
| 🕸️ 知识图谱 | 可视化知识点依赖关系（力导向图） |
| 📈 学习进度 | 掌握度列表 + 学习里程碑 |
| 📊 数据分析 | 雷达图 / 学习时长趋势 / 活动分布 |

### 4.7 切换学段/学科

点击顶部导航栏左侧的下拉菜单，可切换：
- 高中数学 / 高中物理 / 高中化学
- 初中英语 / 初中数学
- 小学数学
- 计算机科学

切换后知识画像和学习计划会自动适配。

---

## 五、停止服务

在运行 `deploy.bat` 的命令行窗口中按 `Ctrl + C` 即可停止服务。

---

## 六、常见问题

### Q1：双击 deploy.bat 后闪退

**A**：通常是 Python 没有安装或不在 PATH 中。打开命令行输入 `python --version` 确认。如果没装，从 python.org 安装 Python 3.10-3.12，安装时勾选 "Add Python to PATH"。

### Q2：启动后浏览器打开是空白页

**A**：等待几秒让后端完全启动。如果一直空白，检查命令行窗口是否有报错信息。手动访问 `http://localhost:8000/api/v1/health` 确认后端是否正常。

### Q3：AI 教练回复"资料不足"

**A**：这说明教辅资料库中没有找到与问题相关度足够的内容。尝试换一个更具体的问题，或确认 `data/` 目录中的数据库文件完整。

### Q4：Magic Notes 生成失败

**A**：Magic Notes 需要连接 AI 大模型。如果 `.env` 中的 API Key 已过期或无效，会生成失败。请联系管理员在后台更新 API Key。

### Q5：端口 8000 被占用

**A**：说明已有其他程序占用了 8000 端口。关闭占用该端口的程序后重试，或编辑 `deploy.bat` 将 `--port 8000` 改为其他端口（如 `--port 8001`）。

### Q6：如何重置到初始演示数据

**A**：停止服务后，删除 `data/edumind.db` 和 `data/qdrant_storage/` 文件夹，然后运行：
```
venv\Scripts\python.exe scripts\seed_demo_student.py
venv\Scripts\python.exe scripts\seed_resources_v2.py
```
> 注意：seed 脚本必须在后端停止状态下运行（Qdrant 文件锁）。

### Q7：苏格拉底模式和普通模式有什么区别

**A**：
- **普通模式**：AI 直接给出讲解和答案
- **苏格拉底模式**：AI 不直接给答案，而是用提问一步步引导你自己推导
- 两种模式可以随时切换，不影响对话历史

---

## 七、技术架构简述

```
用户浏览器 (http://localhost:8000)
    │
    ▼
FastAPI 后端 (Port 8000)
    ├── REST API (/api/v1/...)
    ├── 静态前端托管 (frontend/dist/)
    ├── RAG 检索增强 (Qdrant 向量库)
    ├── LLM 服务 (DeepSeek API)
    └── SQLite 数据库 (data/edumind.db)
```

**技术栈**：FastAPI + Vue 3 + Qdrant + DeepSeek + SQLite

---

## 八、目录结构说明

```
EduMind/
├── deploy.bat              ← 一键启动脚本
├── .env                    ← 环境配置（含 API Key）
├── requirements.txt        ← Python 依赖清单
├── backend/                ← 后端源码
│   ├── main.py             ← FastAPI 入口
│   ├── api/                ← API 路由
│   ├── llm/                ← LLM 服务 + Prompt 模板
│   ├── rag/                ← RAG 检索（Hybrid + Rerank）
│   ├── application/        ← 业务编排器
│   └── ...
├── frontend/
│   └── dist/               ← 预构建前端（浏览器直接加载）
├── data/
│   ├── edumind.db          ← SQLite 数据库
│   └── qdrant_storage/     ← Qdrant 向量库
├── scripts/                ← 数据初始化脚本
└── venv/                   ← Python 虚拟环境（首次运行自动创建）
```

---

*EduMind Team © 2026 | AI-Powered Personalized Learning Platform*
