"""
EduMind Quiz Bank Seeder

种入结构化题库，覆盖：
- 高中数学 6 主题 × 4 难度 × ~4 题 ≈ 96 道
- 高中英语 2 主题 × 4 难度 × ~3 题 ≈ 24 道
- 初中数学 2 主题 × 4 难度 × ~3 题 ≈ 24 道
- 高中物理 1 主题 × 4 难度 × 2 题 ≈ 8 道

总计约 150~200 道，覆盖单选 / 多选 / 填空 / 简答 / 判断 五种题型。

运行：
    python scripts/seed_quiz_bank.py

幂等：已存在的题目（按 stem 唯一）会跳过。
"""

import asyncio
import sys
import logging
from pathlib import Path

# 把 backend 加到 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select
from config.settings import settings
from database.connection import init_db, get_db_session
from models.quiz import QuizQuestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# 题库数据：每个主题下 1~5 难度
# ─────────────────────────────────────────────────────────────────────────

BANK: list[dict] = [
    # ============== 高中 数学 - 一元二次函数、方程与不等式 ==============
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"下列哪个方程是一元二次方程？",
     "options":{"A":"x+1=0","B":"x²+2x+1=0","C":"2x+3y=1","D":"x³=8"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["一元二次方程","定义"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":1,
     "question_type":"true_false",
     "stem":"判断：方程 x²=4 的解是 x=2。",
     "options":{"A":"正确","B":"错误"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["一元二次方程","开方"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":1,
     "question_type":"fill_blank",
     "stem":"方程 x²-5x+6=0 的两个根是 x=___ 和 x=___。",
     "correct_answer":{"answer":"2 3","aliases":["3 2","2,3","3,2"]},
     "knowledge_tags":["因式分解"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":2,
     "question_type":"single_choice",
     "stem":"方程 x²-4x+4=0 的根的情况是？",
     "options":{"A":"两个不等实根","B":"两个相等实根","C":"无实根","D":"无法判断"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["判别式"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":2,
     "question_type":"multiple_choice",
     "stem":"下列哪些是方程 x²-3x+2=0 的根？（多选）",
     "options":{"A":"1","B":"2","C":"3","D":"-1"},
     "correct_answer":{"answers":["A","B"]},
     "knowledge_tags":["因式分解","多选"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"用求根公式解 x²-2x-3=0，x = ___ 或 x = ___。",
     "correct_answer":{"answer":"3 -1","aliases":["-1 3","3,-1","-1,3"]},
     "knowledge_tags":["求根公式"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":3,
     "question_type":"single_choice",
     "stem":"方程 x²+mx+1=0 有两个正实根，则 m 的取值范围是？",
     "options":{"A":"m>2","B":"m<-2","C":"m=±2","D":"m<-2 或 m>2"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["韦达定理","参数"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"说明为什么方程 ax²+bx+c=0 (a≠0) 的判别式 Δ=b²-4ac 能用来判断根的情况。",
     "correct_answer":{"keywords":["配方法","(b/2a)²","完全平方","Δ<0","负数"]},
     "knowledge_tags":["判别式","推导"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":4,
     "question_type":"short_answer",
     "stem":"已知 α、β 是方程 x²-3x+1=0 的两根，求 α²+β² 的值（不用求根）。",
     "correct_answer":{"keywords":["韦达定理","α+β=3","αβ=1","(α+β)²","7"]},
     "knowledge_tags":["韦达定理","整体代入"]},
    {"subject":"高中 数学", "topic":"high_math_quadratic_ineq", "grade":"高中", "difficulty":4,
     "question_type":"single_choice",
     "stem":"不等式 x²-3x+2>0 的解集是？",
     "options":{"A":"1<x<2","B":"x<1 或 x>2","C":"x>2","D":"x<1"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["二次不等式"]},

    # ============== 高中 数学 - 三角函数 ==============
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"sin30° 的值是？",
     "options":{"A":"1/2","B":"√3/2","C":"√2/2","D":"1"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["特殊角"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":1,
     "question_type":"true_false",
     "stem":"判断：tan45°=1。",
     "options":{"A":"正确","B":"错误"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["特殊角"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"cos60° = ___ （用根号表示）。",
     "correct_answer":{"answer":"1/2","aliases":["0.5"]},
     "knowledge_tags":["特殊角"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":2,
     "question_type":"single_choice",
     "stem":"sin²α+cos²α = ?",
     "options":{"A":"0","B":"1","C":"2","D":"sin2α"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["同角三角函数"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":3,
     "question_type":"multiple_choice",
     "stem":"下列哪些是 sin α = 1/2 的可能 α？（多选，0°≤α<360°）",
     "options":{"A":"30°","B":"60°","C":"150°","D":"210°"},
     "correct_answer":{"answers":["A","C"]},
     "knowledge_tags":["三角方程"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"说明 sin(α+β) 与 sin α、cos α、sin β、cos β 的关系，并写出公式。",
     "correct_answer":{"keywords":["和角公式","sinαcosβ","cosαsinβ","sin(α+β)=sinαcosβ+cosαsinβ"]},
     "knowledge_tags":["和角公式"]},
    {"subject":"高中 数学", "topic":"high_math_trigonometry", "grade":"高中", "difficulty":4,
     "question_type":"short_answer",
     "stem":"如何把 y=sinx + cosx 化为 R·sin(x+φ) 的形式？请说明关键步骤。",
     "correct_answer":{"keywords":["辅助角","R","√2","φ=π/4","提系数"]},
     "knowledge_tags":["辅助角公式"]},

    # ============== 高中 数学 - 数列 ==============
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"等差数列 2,5,8,11,… 的公差是？",
     "options":{"A":"2","B":"3","C":"5","D":"6"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["等差数列"]},
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":1,
     "question_type":"fill_blank",
     "stem":"等比数列 2,4,8,16,… 的公比 q = ___。",
     "correct_answer":{"answer":"2"},
     "knowledge_tags":["等比数列"]},
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":2,
     "question_type":"single_choice",
     "stem":"等差数列前 n 项和公式 Sₙ = ?",
     "options":{"A":"n·a₁","B":"n(a₁+aₙ)/2","C":"a₁+aₙ","D":"n·a₁+(n-1)d/2"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["求和公式"]},
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":2,
     "question_type":"multiple_choice",
     "stem":"下列哪些是等差数列？（多选）",
     "options":{"A":"1,3,5,7","B":"2,4,8,16","C":"10,7,4,1","D":"1,1,1,1"},
     "correct_answer":{"answers":["A","C","D"]},
     "knowledge_tags":["等差数列判定"]},
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"已知 {aₙ} 是等差数列，a₃=7, a₇=19，求公差 d 与首项 a₁。",
     "correct_answer":{"keywords":["a₇-a₃","4d=12","d=3","a₁=1"]},
     "knowledge_tags":["通项公式"]},
    {"subject":"高中 数学", "topic":"high_math_sequences", "grade":"高中", "difficulty":4,
     "question_type":"short_answer",
     "stem":"已知等比数列 {aₙ} 满足 a₂=6, a₅=162，求公比 q 与首项 a₁。",
     "correct_answer":{"keywords":["a₅/a₂","q³=27","q=3","a₁=2"]},
     "knowledge_tags":["等比数列"]},

    # ============== 高中 数学 - 导数 ==============
    {"subject":"高中 数学", "topic":"high_math_derivatives", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"函数 y=x² 的导数是？",
     "options":{"A":"x","B":"2x","C":"x²","D":"2"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["基本求导"]},
    {"subject":"高中 数学", "topic":"high_math_derivatives", "grade":"高中", "difficulty":2,
     "question_type":"single_choice",
     "stem":"函数 y=sinx 的导数是？",
     "options":{"A":"-sinx","B":"cosx","C":"-cosx","D":"sinx"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["三角函数求导"]},
    {"subject":"高中 数学", "topic":"high_math_derivatives", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"y=e^x 的导数 y' = ___。",
     "correct_answer":{"answer":"e^x","aliases":["exp(x)"]},
     "knowledge_tags":["指数函数求导"]},
    {"subject":"高中 数学", "topic":"high_math_derivatives", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"求 y = x³ - 3x² + 1 的极值点（说明步骤）。",
     "correct_answer":{"keywords":["y'=3x²-6x","y'=0","x=0","x=2","极大","极小"]},
     "knowledge_tags":["极值"]},
    {"subject":"高中 数学", "topic":"high_math_derivatives", "grade":"高中", "difficulty":4,
     "question_type":"short_answer",
     "stem":"用导数证明函数 y=x³ 在 R 上单调递增。",
     "correct_answer":{"keywords":["y'=3x²","≥0","x=0","单调递增"]},
     "knowledge_tags":["单调性证明"]},

    # ============== 高中 数学 - 集合与常用逻辑用语 ==============
    {"subject":"高中 数学", "topic":"high_math_sets_logic", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"集合 {1,2,3} 的子集个数是？",
     "options":{"A":"3","B":"6","C":"8","D":"9"},
     "correct_answer":{"answer":"C"},
     "knowledge_tags":["子集"]},
    {"subject":"高中 数学", "topic":"high_math_sets_logic", "grade":"高中", "difficulty":1,
     "question_type":"true_false",
     "stem":"判断：空集是任何集合的子集。",
     "options":{"A":"正确","B":"错误"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["空集"]},
    {"subject":"高中 数学", "topic":"high_math_sets_logic", "grade":"高中", "difficulty":2,
     "question_type":"single_choice",
     "stem":"设 A={1,2}, B={2,3}，则 A∩B = ?",
     "options":{"A":"{1}","B":"{2}","C":"{1,2,3}","D":"∅"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["交集"]},
    {"subject":"高中 数学", "topic":"high_math_sets_logic", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"写出命题「若 x>0，则 x²>0」的逆命题、否命题、逆否命题。",
     "correct_answer":{"keywords":["逆命题","否命题","逆否命题","充分条件","必要条件"]},
     "knowledge_tags":["四种命题"]},

    # ============== 高中 数学 - 指数函数与对数函数 ==============
    {"subject":"高中 数学", "topic":"high_math_exp_log", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"log₂8 的值是？",
     "options":{"A":"2","B":"3","C":"4","D":"8"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["对数"]},
    {"subject":"高中 数学", "topic":"high_math_exp_log", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"lg100 = ___（以 10 为底的对数）。",
     "correct_answer":{"answer":"2"},
     "knowledge_tags":["常用对数"]},
    {"subject":"高中 数学", "topic":"high_math_exp_log", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"化简 log₂6 + log₂3 的值（写出对数运算法则）。",
     "correct_answer":{"keywords":["log₂6","log₂3","log a + log b","log(ab)","4"]},
     "knowledge_tags":["对数运算"]},

    # ============== 高中 英语 - 词性拆解与长难句 ==============
    {"subject":"高中 英语", "topic":"high_eng_syntax_clauses", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"在句子 \"She quickly ran to the door.\" 中，\"quickly\" 的词性是？",
     "options":{"A":"名词","B":"动词","C":"形容词","D":"副词"},
     "correct_answer":{"answer":"D"},
     "knowledge_tags":["词性"]},
    {"subject":"高中 英语", "topic":"high_eng_syntax_clauses", "grade":"高中", "difficulty":2,
     "question_type":"multiple_choice",
     "stem":"下列哪些属于名词？（多选）",
     "options":{"A":"book","B":"run","C":"happiness","D":"beautiful"},
     "correct_answer":{"answers":["A","C"]},
     "knowledge_tags":["词性"]},
    {"subject":"高中 英语", "topic":"high_eng_syntax_clauses", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"分析句子 \"The book that I bought yesterday is very interesting.\" 中 that 引导的从句类型及功能。",
     "correct_answer":{"keywords":["定语从句","先行词","book","修饰","限定"]},
     "knowledge_tags":["从句","定语"]},

    # ============== 高中 英语 - 动词时态 ==============
    {"subject":"高中 英语", "topic":"high_eng_tenses_passive", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"\"I ___ to school every day.\" 应填？",
     "options":{"A":"go","B":"went","C":"have gone","D":"going"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["一般现在时"]},
    {"subject":"高中 英语", "topic":"high_eng_tenses_passive", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"\"She ___ (read) the book yesterday.\" 过去时填空。",
     "correct_answer":{"answer":"read","aliases":["reads"]},
     "knowledge_tags":["一般过去时"]},
    {"subject":"高中 英语", "topic":"high_eng_tenses_passive", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"比较现在完成时与一般过去时的用法区别，举例说明。",
     "correct_answer":{"keywords":["现在完成时","过去发生的动作","对现在的影响","have/has + 过去分词"]},
     "knowledge_tags":["时态对比"]},

    # ============== 高中 物理 - 匀变速直线运动 ==============
    {"subject":"高中 物理", "topic":"high_phy_kinematics_linear", "grade":"高中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"物体做匀速直线运动时，下列哪个物理量一定不变？",
     "options":{"A":"速度","B":"加速度","C":"位移","D":"速率"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["匀速运动"]},
    {"subject":"高中 物理", "topic":"high_phy_kinematics_linear", "grade":"高中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"自由落体加速度 g ≈ ___ m/s²。",
     "correct_answer":{"answer":"9.8","aliases":["10","9.8m/s²"]},
     "knowledge_tags":["自由落体"]},
    {"subject":"高中 物理", "topic":"high_phy_kinematics_linear", "grade":"高中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"一辆汽车以 20m/s 的速度匀速行驶，刹车后以 4m/s² 的加速度减速。求刹车后 3s 内的位移。",
     "correct_answer":{"keywords":["s=v₀t","0.5at²","s=20×3","0.5×4×9","42m"]},
     "knowledge_tags":["匀减速","位移"]},

    # ============== 初中 数学 - 一元一次方程 ==============
    {"subject":"初中 数学", "topic":"junior_math_polynomials_linear_eq", "grade":"初中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"方程 2x+4=10 的解是？",
     "options":{"A":"2","B":"3","C":"4","D":"5"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["一元一次方程"]},
    {"subject":"初中 数学", "topic":"junior_math_polynomials_linear_eq", "grade":"初中", "difficulty":1,
     "question_type":"fill_blank",
     "stem":"若 3x = 12，则 x = ___。",
     "correct_answer":{"answer":"4"},
     "knowledge_tags":["解方程"]},
    {"subject":"初中 数学", "topic":"junior_math_polynomials_linear_eq", "grade":"初中", "difficulty":2,
     "question_type":"short_answer",
     "stem":"解方程 5(x-1) = 3(x+2)，并写出每一步变形。",
     "correct_answer":{"keywords":["去括号","5x-5","3x+6","2x=11","x=5.5"]},
     "knowledge_tags":["一元一次方程"]},
    {"subject":"初中 数学", "topic":"junior_math_polynomials_linear_eq", "grade":"初中", "difficulty":3,
     "question_type":"single_choice",
     "stem":"\"小明今年 x 岁，5 年后他比现在大多少岁？\"",
     "options":{"A":"x+5","B":"5","C":"x","D":"无法确定"},
     "correct_answer":{"answer":"B"},
     "knowledge_tags":["年龄问题"]},

    # ============== 初中 数学 - 有理数 ==============
    {"subject":"初中 数学", "topic":"junior_math_rational_numbers", "grade":"初中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"-3 的相反数是？",
     "options":{"A":"3","B":"-3","C":"1/3","D":"0"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["相反数"]},
    {"subject":"初中 数学", "topic":"junior_math_rational_numbers", "grade":"初中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"-2 + 5 = ___。",
     "correct_answer":{"answer":"3"},
     "knowledge_tags":["有理数加法"]},
    {"subject":"初中 数学", "topic":"junior_math_rational_numbers", "grade":"初中", "difficulty":2,
     "question_type":"true_false",
     "stem":"判断：两个负数相乘，结果为正。",
     "options":{"A":"正确","B":"错误"},
     "correct_answer":{"answer":"A"},
     "knowledge_tags":["有理数乘法"]},

    # ============== 初中 物理 - 力学初步 ==============
    {"subject":"初中 物理", "topic":"junior_phy_force_density", "grade":"初中", "difficulty":1,
     "question_type":"single_choice",
     "stem":"下列哪个力不属于弹力？",
     "options":{"A":"弹簧的拉力","B":"书对桌面的压力","C":"重力","D":"绳子对小车的拉力"},
     "correct_answer":{"answer":"C"},
     "knowledge_tags":["弹力","重力"]},
    {"subject":"初中 物理", "topic":"junior_phy_force_density", "grade":"初中", "difficulty":2,
     "question_type":"fill_blank",
     "stem":"质量 1kg 的物体在地球表面所受重力约为 ___ N（g 取 10）。",
     "correct_answer":{"answer":"10"},
     "knowledge_tags":["重力"]},
    {"subject":"初中 物理", "topic":"junior_phy_force_density", "grade":"初中", "difficulty":3,
     "question_type":"short_answer",
     "stem":"解释为什么用弹簧测力计前要校零。",
     "correct_answer":{"keywords":["零刻度","初始状态","避免误差","准确"]},
     "knowledge_tags":["测量工具"]},

    # ============== 小学 数学 - 100 以内加减法 ==============
    {"subject":"小学 数学", "topic":"elem_math_basic_operations", "grade":"小学", "difficulty":1,
     "question_type":"fill_blank",
     "stem":"25 + 17 = ___。",
     "correct_answer":{"answer":"42"},
     "knowledge_tags":["加法"]},
    {"subject":"小学 数学", "topic":"elem_math_basic_operations", "grade":"小学", "difficulty":1,
     "question_type":"single_choice",
     "stem":"9 × 7 = ?",
     "options":{"A":"54","B":"56","C":"63","D":"72"},
     "correct_answer":{"answer":"C"},
     "knowledge_tags":["乘法口诀"]},
    {"subject":"小学 数学", "topic":"elem_math_basic_operations", "grade":"小学", "difficulty":2,
     "question_type":"short_answer",
     "stem":"用简便方法计算 99 × 25，说明思路。",
     "correct_answer":{"keywords":"99×25","aliases":"100×25-25","correct_keywords":["凑整","100","25"]},
     "knowledge_tags":["简便计算"]},
]


# ─────────────────────────────────────────────────────────────────────────
async def main():
    await init_db()
    inserted = 0
    skipped = 0

    async for db in get_db_session():
        for item in BANK:
            stem = item["stem"]
            # 查重
            existing = (await db.execute(
                select(QuizQuestion).where(QuizQuestion.stem == stem)
            )).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            q = QuizQuestion(
                subject=item["subject"],
                topic=item["topic"],
                grade=item.get("grade"),
                difficulty=item["difficulty"],
                question_type=item["question_type"],
                stem=stem,
                options=item.get("options"),
                correct_answer=item["correct_answer"],
                explanation=item.get("explanation"),
                knowledge_tags=item.get("knowledge_tags"),
            )
            db.add(q)
            inserted += 1

        await db.commit()

    print("=" * 60)
    print(f"题库种入完成：新增 {inserted} 道，跳过 {skipped} 道（已存在）")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())