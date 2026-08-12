"""
EduMind Resources Seeder

把教辅片段写入 learning_resources 表并向量化入 Qdrant。

覆盖 demo 实际会问到的知识点（与 quiz_questions 配套）：
- 高中数学 5 大主题
- 高中英语 2 大主题
- 初中数学 2 大主题
- 高中物理 1 大主题
- 拓展：函数、几何、化学、生物等

每条 ≤ 400 字，RAG 上下文窗口友好。

运行：
    python scripts/seed_resources.py

幂等：按 title + content 唯一性查重。
"""

import asyncio
import sys
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select
from config.settings import settings
from database.connection import init_db, get_db_session
from models.resource import LearningResource
from services.embedding import embedding_service
from rag import rag_module

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# 教辅片段库
# ─────────────────────────────────────────────────────────────────────────

RESOURCES: list[dict] = [
    # ─────────── 高中 数学 ───────────
    {
        "subject": "高中 数学", "topic": "high_math_quadratic_ineq",
        "title": "一元二次方程的求根公式",
        "source": "人教版高中数学必修一 §3.2",
        "content": (
            "对于一元二次方程 ax²+bx+c=0（a≠0），其解可以用求根公式表达："
            "x = (-b ± √(b²-4ac)) / (2a)。其中判别式 Δ = b²-4ac 决定了根的情况："
            "Δ>0 时有两个不等实根；Δ=0 时有两个相等实根（重根）；Δ<0 时无实根。"
            "解一元二次方程的标准步骤：(1) 化为标准形式 ax²+bx+c=0；"
            "(2) 套公式计算 Δ；(3) 根据 Δ 判断根的情况并写出解。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_quadratic_ineq",
        "title": "韦达定理与根的关系",
        "source": "人教版高中数学必修一 §3.3",
        "content": (
            "对于方程 ax²+bx+c=0 的两个根 x₁、x₂，韦达定理指出："
            "x₁+x₂ = -b/a，x₁·x₂ = c/a。利用韦达定理可以在不解方程的情况下"
            "求出两根之和与两根之积。例如：已知 α+β=3, αβ=2，"
            "可构造方程 x²-3x+2=0 得到根 α=1, β=2。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_quadratic_ineq",
        "title": "二次不等式的解法",
        "source": "人教版高中数学必修一 §3.4",
        "content": (
            "解一元二次不等式 ax²+bx+c>0 的关键是：(1) 求对应方程 ax²+bx+c=0 的根；"
            "(2) a>0 时，抛物线开口向上，不等式解集在两根外侧；"
            "(3) a<0 时，抛物线开口向下，解集在两根之间。"
            "示例：x²-3x+2>0 → (x-1)(x-2)>0 → x<1 或 x>2。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_trigonometry",
        "title": "特殊角的三角函数值",
        "source": "人教版高中数学必修四 §1.2",
        "content": (
            "常见特殊角的三角函数值："
            "sin30°=1/2, sin45°=√2/2, sin60°=√3/2；"
            "cos30°=√3/2, cos45°=√2/2, cos60°=1/2；"
            "tan30°=√3/3, tan45°=1, tan60°=√3。"
            "记忆口诀：30°、45°、60° 的 sin 与 cos 互相对换，"
            "tan 等于 sin 除以 cos。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_trigonometry",
        "title": "和角公式 sin(α+β)",
        "source": "人教版高中数学必修四 §3.1",
        "content": (
            "sin(α+β) = sin α cos β + cos α sin β。"
            "类似地：cos(α+β) = cos α cos β - sin α sin β；"
            "tan(α+β) = (tan α + tan β) / (1 - tan α tan β)。"
            "这些公式的推导可使用单位圆上两角相加的几何意义。"
            "应用：化简形如 y = a sin x + b cos x 的函数为"
            "y = √(a²+b²) · sin(x+φ)。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_sequences",
        "title": "等差数列的通项与求和",
        "source": "人教版高中数学必修五 §2.1",
        "content": (
            "等差数列：相邻两项之差为常数（公差 d）。"
            "通项公式：aₙ = a₁ + (n-1)d。"
            "前 n 项和：Sₙ = n(a₁+aₙ)/2 = na₁ + n(n-1)d/2。"
            "判定方法：若 aₙ₊₁ - aₙ = 常数则为等差数列。"
            "应用：已知 a₃=7, a₇=19，由 d=(a₇-a₃)/4=3 反推 a₁=1。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_sequences",
        "title": "等比数列与通项公式",
        "source": "人教版高中数学必修五 §2.3",
        "content": (
            "等比数列：相邻两项之比为常数（公比 q≠0）。"
            "通项公式：aₙ = a₁ · q^(n-1)。"
            "前 n 项和：当 q≠1 时 Sₙ = a₁(1-q^n)/(1-q)；"
            "当 q=1 时 Sₙ = na₁。"
            "应用：已知 a₂=6, a₅=162，由 q³=a₅/a₂=27 得 q=3。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_derivatives",
        "title": "基本求导公式与法则",
        "source": "人教版高中数学选修二 §1.2",
        "content": (
            "常用求导公式：(xⁿ)' = n·xⁿ⁻¹；(sin x)' = cos x；"
            "(cos x)' = -sin x；(eˣ)' = eˣ；(ln x)' = 1/x。"
            "四则运算法则：(u±v)' = u'±v'；(uv)' = u'v+uv'；(u/v)' = (u'v-uv')/v²。"
            "复合函数求导（链式法则）：[f(g(x))]' = f'(g(x)) · g'(x)。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_derivatives",
        "title": "用导数判断单调性与极值",
        "source": "人教版高中数学选修二 §1.3",
        "content": (
            "单调性判别：f'(x)>0 时 f(x) 单调递增；f'(x)<0 时 f(x) 单调递减；"
            "f'(x)=0 的点（驻点）处单调性可能变化。"
            "极值判定：(1) 求 f'(x)=0 的解；(2) 判断驻点两侧 f'(x) 符号变化；"
            "若左负右正为极小，左正右负为极大。"
            "例：y=x³-3x²+1 的导数 y'=3x²-6x=3x(x-2)，驻点 x=0, x=2。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_sets_logic",
        "title": "集合的基本运算",
        "source": "人教版高中数学必修一 §1.2",
        "content": (
            "集合的三大基本运算：(1) 交集 A∩B = {x | x∈A 且 x∈B}；"
            "(2) 并集 A∪B = {x | x∈A 或 x∈B}；"
            "(3) 补集（相对于全集 U）：∁ᵤA = {x | x∈U 且 x∉A}。"
            "空集 ∅ 是任何集合的子集；n 元素集合有 2ⁿ 个子集。"
        ),
    },
    {
        "subject": "高中 数学", "topic": "high_math_exp_log",
        "title": "对数运算法则",
        "source": "人教版高中数学必修一 §4.2",
        "content": (
            "对数定义：若 aˣ = N (a>0, a≠1)，则 x = logₐN。"
            "基本性质：(1) logₐ(MN) = logₐM + logₐN；"
            "(2) logₐ(M/N) = logₐM - logₐN；"
            "(3) logₐ(Mⁿ) = n·logₐM。"
            "常用值：log₂8=3, log₂4=2, lg100=2 (常用对数 base=10)。"
        ),
    },

    # ─────────── 高中 英语 ───────────
    {
        "subject": "高中 英语", "topic": "high_eng_syntax_clauses",
        "title": "英语八大词性与句子成分",
        "source": "人教版高中英语必修一 §1",
        "content": (
            "英语八大词性：名词(n.)、动词(v.)、形容词(adj.)、副词(adv.)、"
            "代词(pron.)、介词(prep.)、连词(conj.)、冠词(art.)。"
            "基本句型：(1) 主+谓；(2) 主+谓+宾；(3) 主+谓+间宾+直宾；"
            "(4) 主+谓+宾+宾补；(5) 主+系+表。"
            "例：She quickly ran to the door 中 quickly 是副词，修饰动词 ran。"
        ),
    },
    {
        "subject": "高中 英语", "topic": "high_eng_tenses_passive",
        "title": "英语十二大时态对比",
        "source": "人教版高中英语必修二 §2",
        "content": (
            "高中阶段重点掌握 8 种时态："
            "(1) 一般现在：表示习惯、客观事实；(2) 一般过去：过去发生的事；"
            "(3) 现在进行：此刻正在发生；(4) 现在完成：过去发生且对现在有影响；"
            "(5) 一般将来：将要做的事；(6) 过去进行：过去某时正在发生；"
            "(7) 过去完成：过去某时之前已完成；(8) 过去将来：过去的将来。"
            "现在完成时与一般过去时的区别：现在完成强调'对现在的影响'，"
            "一般过去强调'过去某时发生'，常与具体过去时间状语连用。"
        ),
    },

    # ─────────── 高中 物理 ───────────
    {
        "subject": "高中 物理", "topic": "high_phy_kinematics_linear",
        "title": "匀变速直线运动公式",
        "source": "人教版高中物理必修一 §2",
        "content": (
            "匀变速直线运动核心公式（v₀ 初速度，v 末速度，a 加速度，t 时间）："
            "(1) 速度公式：v = v₀ + at；"
            "(2) 位移公式：s = v₀t + ½at²；"
            "(3) 速度位移关系：v² - v₀² = 2as；"
            "(4) 平均速度：v̄ = (v₀+v)/2 = s/t。"
            "自由落体是 a=g≈9.8 m/s², v₀=0 的特例。"
        ),
    },

    # ─────────── 初中 数学 ───────────
    {
        "subject": "初中 数学", "topic": "junior_math_polynomials_linear_eq",
        "title": "一元一次方程的解法步骤",
        "source": "人教版初中数学七年级上 §3",
        "content": (
            "解一元一次方程的标准步骤（去分母 → 去括号 → 移项 → 合并同类项 → 系数化为1）："
            "例：解 5(x-1) = 3(x+2)。"
            "(1) 去括号：5x - 5 = 3x + 6；"
            "(2) 移项：5x - 3x = 6 + 5；"
            "(3) 合并：2x = 11；(4) 系数化为1：x = 5.5。"
        ),
    },
    {
        "subject": "初中 数学", "topic": "junior_math_rational_numbers",
        "title": "有理数运算规则",
        "source": "人教版初中数学七年级上 §1",
        "content": (
            "有理数包括正数、负数、零。运算法则："
            "(1) 同号相加取相同符号；"
            "(2) 异号相加取绝对值大的符号；"
            "(3) 两负数相乘得正；异号相乘得负；零乘任何数得零。"
            "相反数：a 的相反数是 -a（数轴上关于原点对称）。"
        ),
    },

    # ─────────── 拓展（与现有英文教辅配套）───────────
    {
        "subject": "通用", "topic": "study_skills",
        "title": "费曼学习法：用讲解代替死记",
        "source": "学习科学经典方法",
        "content": (
            "费曼学习法四步：(1) 选择一个概念；(2) 假装在向别人讲解；"
            "(3) 卡住时回去重新学习；(4) 简化语言并用类比。"
            "核心思想：能简单讲清楚才是真的懂。对应的 EduMind 实践："
            "在 AI 教练的'讲解'环节，让学生用自己的话复述概念，"
            "AI 评估讲解的准确性与完整性。"
        ),
    },
    {
        "subject": "通用", "topic": "study_skills",
        "title": "艾宾浩姆遗忘曲线与间隔重复",
        "source": "学习科学经典方法",
        "content": (
            "艾宾浩姆曲线表明：学完 20 分钟后遗忘 42%，1 天后遗忘 66%。"
            "应对方法是'间隔重复'：第 1 天复习 1 次、第 2 天 1 次、"
            "第 7 天 1 次、第 30 天 1 次。EduMind 的'错题本 + 今日复习'功能"
            "即基于此设计：错题会按时间间隔出现在复习列表里。"
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────

async def main():
    await init_db()
    inserted = 0
    skipped = 0
    failed = 0

    async for db in get_db_session():
        # 1) 查重准备
        for item in RESOURCES:
            existing = (await db.execute(
                select(LearningResource).where(
                    (LearningResource.parent_doc == item["title"])
                    | (LearningResource.title == item["title"])
                )
            )).scalars().first()
            if existing:
                skipped += 1
                continue

            # 2) 编码 + 写入 Qdrant + 写 DB（按 chunk 切分）
            try:
                chunks = await rag_module.upsert_document(
                    db=db,
                    title=item["title"],
                    subject=item["subject"],
                    topic=item["topic"],
                    content=item["content"],
                    source=item.get("source"),
                )
                inserted += 1
                logger.info(f"✓ {item['title']} ({len(chunks)} chunk(s), first id={chunks[0].id})")
            except Exception as exc:
                failed += 1
                logger.error(f"✗ {item['title']}: {exc}")

        await db.commit()

    print("=" * 60)
    print(f"教辅片段种入完成：新增 {inserted} 条 / 跳过 {skipped} 条 / 失败 {failed} 条")
    print(f"collection = {settings.qdrant_collection_name}")
    print(f"dimensions = {settings.embedding_dimensions}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())