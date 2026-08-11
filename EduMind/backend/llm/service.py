"""
EduMind LLM Service

Manages interactions with DeepSeek or compatible OpenAI-compatible LLM endpoints.
Handles chat completions, concept explanations, history summarization, and mock fallbacks.
"""

import logging
import httpx
from config.settings import settings
from services.model_config import model_config_service
from llm.prompts import (
    COACH_SYSTEM_PROMPT,
    CHAT_PROMPT_TEMPLATE,
    CHAT_PROMPT_TEMPLATE_NO_CONTEXT,
    EXPLAIN_PROMPT_TEMPLATE,
    EXPLAIN_PROMPT_TEMPLATE_NO_CONTEXT,
    SUMMARIZE_PROMPT_TEMPLATE,
    GENERATE_CURRICULUM_PROMPT,
    GENERATE_QUIZ_PROMPT,
    GENERATE_STRUCTURED_QUIZ_PROMPT,
    GRADE_QUIZ_PROMPT,
)
from core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

# Predefined rich curriculum topology maps for fallback or standard subjects
PREDEFINED_CURRICULA = {
    # ── 高中 数学 (10大核心章节) ──────────────────────────────────────────────
    "高中 数学": {
        "__zh_names__": {
            "high_math_sets_logic": "1. 集合与常用逻辑用语",
            "high_math_quadratic_ineq": "2. 一元二次函数、方程与不等式",
            "high_math_exp_log": "3. 指数函数与对数函数",
            "high_math_trigonometry": "4. 三角函数与解三角形",
            "high_math_vectors_complex": "5. 平面向量与复数",
            "high_math_solid_geometry": "6. 立体几何与空间向量",
            "high_math_lines_circles": "7. 直线与圆的方程",
            "high_math_conic_sections": "8. 圆锥曲线(椭圆/双曲线/抛物线)",
            "high_math_sequences": "9. 数列与归纳推理",
            "high_math_derivatives": "10. 导数及其在函数中的应用"
        },
        "high_math_sets_logic": [],
        "high_math_quadratic_ineq": ["high_math_sets_logic"],
        "high_math_exp_log": ["high_math_quadratic_ineq"],
        "high_math_trigonometry": ["high_math_exp_log"],
        "high_math_vectors_complex": ["high_math_trigonometry"],
        "high_math_solid_geometry": ["high_math_vectors_complex"],
        "high_math_lines_circles": ["high_math_quadratic_ineq"],
        "high_math_conic_sections": ["high_math_lines_circles"],
        "high_math_sequences": ["high_math_quadratic_ineq"],
        "high_math_derivatives": ["high_math_exp_log", "high_math_sequences"]
    },

    # ── 高中 英语 (8大核心章节) ───────────────────────────────────────────────
    "高中 英语": {
        "__zh_names__": {
            "high_eng_syntax_clauses": "1. 词性拆解与长难句结构分析",
            "high_eng_tenses_passive": "2. 动词时态、语态与被动表达",
            "high_eng_attributive_noun_clauses": "3. 定语从句与名词性从句精讲",
            "high_eng_adverbial_subjunctive": "4. 状语从句与虚拟语气应用",
            "high_eng_non_finite_verbs": "5. 非谓语动词(分词/动名词/不定式)",
            "high_eng_reading_strategies": "6. 阅读理解高阶推理与主旨提炼",
            "high_eng_cloze_logic": "7. 完形填空上下文逻辑推断",
            "high_eng_summary_continuation_writing": "8. 概要写作与读后续写实操"
        },
        "high_eng_syntax_clauses": [],
        "high_eng_tenses_passive": ["high_eng_syntax_clauses"],
        "high_eng_attributive_noun_clauses": ["high_eng_syntax_clauses"],
        "high_eng_adverbial_subjunctive": ["high_eng_attributive_noun_clauses"],
        "high_eng_non_finite_verbs": ["high_eng_tenses_passive"],
        "high_eng_reading_strategies": ["high_eng_syntax_clauses"],
        "high_eng_cloze_logic": ["high_eng_reading_strategies"],
        "high_eng_summary_continuation_writing": ["high_eng_non_finite_verbs", "high_eng_reading_strategies"]
    },

    # ── 高中 物理 (9大核心章节) ───────────────────────────────────────────────
    "高中 物理": {
        "__zh_names__": {
            "high_phy_kinematics_linear": "1. 匀变速直线运动与自由落体",
            "high_phy_forces_newton": "2. 相互作用力与牛顿三大运动定律",
            "high_phy_curved_gravitation": "3. 曲线运动、平抛与万有引力",
            "high_phy_work_energy": "4. 功、功率与机械能守恒定律",
            "high_phy_electrostatics": "5. 静电场、电势能与电容器",
            "high_phy_direct_current": "6. 恒定电流与闭合电路欧姆定律",
            "high_phy_magnetic_field": "7. 磁场、安培力与洛伦兹力",
            "high_phy_induction": "8. 电磁感应与法拉第电磁感应定律",
            "high_phy_momentum_collisions": "9. 动量守恒定律与碰撞实验"
        },
        "high_phy_kinematics_linear": [],
        "high_phy_forces_newton": ["high_phy_kinematics_linear"],
        "high_phy_curved_gravitation": ["high_phy_forces_newton"],
        "high_phy_work_energy": ["high_phy_forces_newton"],
        "high_phy_electrostatics": ["high_phy_forces_newton"],
        "high_phy_direct_current": ["high_phy_electrostatics"],
        "high_phy_magnetic_field": ["high_phy_direct_current"],
        "high_phy_induction": ["high_phy_magnetic_field"],
        "high_phy_momentum_collisions": ["high_phy_work_energy"]
    },

    # ── 高中 化学 (8大核心章节) ───────────────────────────────────────────────
    "高中 化学": {
        "__zh_names__": {
            "high_chem_mole_volume": "1. 物质的量与气体摩尔体积",
            "high_chem_periodic_table_bonds": "2. 元素周期律与化学键理论",
            "high_chem_reaction_enthalpy": "3. 化学反应热效应与焓变",
            "high_chem_reaction_equilibrium": "4. 化学反应速率与化学平衡",
            "high_chem_ionic_equilibrium": "5. 水溶液中的离子平衡与 pH 探究",
            "high_chem_electrochemistry": "6. 原电池与电解池电化学基础",
            "high_chem_inorganic_elements": "7. 常见金属与非金属化合物",
            "high_chem_organic_mechanisms": "8. 有机化学基础与官能团推导"
        },
        "high_chem_mole_volume": [],
        "high_chem_periodic_table_bonds": ["high_chem_mole_volume"],
        "high_chem_reaction_enthalpy": ["high_chem_mole_volume"],
        "high_chem_reaction_equilibrium": ["high_chem_reaction_enthalpy"],
        "high_chem_ionic_equilibrium": ["high_chem_reaction_equilibrium"],
        "high_chem_electrochemistry": ["high_chem_ionic_equilibrium"],
        "high_chem_inorganic_elements": ["high_chem_periodic_table_bonds"],
        "high_chem_organic_mechanisms": ["high_chem_periodic_table_bonds"]
    },

    # ── 初中 数学 (7大核心章节) ───────────────────────────────────────────────
    "初中 数学": {
        "__zh_names__": {
            "junior_math_rational_numbers": "1. 有理数与数轴运算法则",
            "junior_math_polynomials_linear_eq": "2. 整式的加减与一元一次方程",
            "junior_math_system_linear_ineq": "3. 二元一次方程组与不等式组",
            "junior_math_lines_triangles": "4. 平行线、相交线与三角形全等",
            "junior_math_factoring_fractions": "5. 因式分解与分式方程",
            "junior_math_functions_intro": "6. 反比例函数与二次函数初步",
            "junior_math_circles_pythagorean": "7. 圆与勾股定理应用"
        },
        "junior_math_rational_numbers": [],
        "junior_math_polynomials_linear_eq": ["junior_math_rational_numbers"],
        "junior_math_system_linear_ineq": ["junior_math_polynomials_linear_eq"],
        "junior_math_lines_triangles": ["junior_math_rational_numbers"],
        "junior_math_factoring_fractions": ["junior_math_polynomials_linear_eq"],
        "junior_math_functions_intro": ["junior_math_system_linear_ineq"],
        "junior_math_circles_pythagorean": ["junior_math_lines_triangles"]
    },

    # ── 初中 英语 (6大核心章节) ───────────────────────────────────────────────
    "初中 英语": {
        "__zh_names__": {
            "junior_eng_parts_of_speech": "1. 八大词性与基本句型结构",
            "junior_eng_basic_tenses": "2. 一般现在时、过去时与进行时",
            "junior_eng_comparatives_modals": "3. 比较级、最高级与情态动词",
            "junior_eng_clauses_intro": "4. 宾语从句与定语从句基础",
            "junior_eng_cloze_reading": "5. 完形填空与日常对话阅读",
            "junior_eng_composition": "6. 情景对话与短文写作"
        },
        "junior_eng_parts_of_speech": [],
        "junior_eng_basic_tenses": ["junior_eng_parts_of_speech"],
        "junior_eng_comparatives_modals": ["junior_eng_basic_tenses"],
        "junior_eng_clauses_intro": ["junior_eng_parts_of_speech"],
        "junior_eng_cloze_reading": ["junior_eng_basic_tenses"],
        "junior_eng_composition": ["junior_eng_clauses_intro"]
    },

    # ── 初中 物理 (6大核心章节) ───────────────────────────────────────────────
    "初中 物理": {
        "__zh_names__": {
            "junior_phy_mechanics_motion": "1. 声现象、物态变化与简单运动",
            "junior_phy_force_density": "2. 质量、密度与力学初步(重力/摩擦力)",
            "junior_phy_pressure_buoyancy": "3. 压强、浮力与阿基米德原理",
            "junior_phy_work_machines": "4. 功、功率与简单机械(杠杆/滑轮)",
            "junior_phy_circuits_ohm": "5. 电路连接与欧姆定律",
            "junior_phy_power_electromagnetism": "6. 电功率与电生磁初步"
        },
        "junior_phy_mechanics_motion": [],
        "junior_phy_force_density": ["junior_phy_mechanics_motion"],
        "junior_phy_pressure_buoyancy": ["junior_phy_force_density"],
        "junior_phy_work_machines": ["junior_phy_pressure_buoyancy"],
        "junior_phy_circuits_ohm": ["junior_phy_mechanics_motion"],
        "junior_phy_power_electromagnetism": ["junior_phy_circuits_ohm"]
    },

    # ── 小学 数学 (5大核心章节) ───────────────────────────────────────────────
    "小学 数学": {
        "__zh_names__": {
            "elem_math_basic_operations": "1. 100以内的加减法与表内乘除法",
            "elem_math_mixed_calc": "2. 四则混合运算与简便计算",
            "elem_math_fractions_decimals": "3. 分数、小数初步与百分数应用",
            "elem_math_area_geometry": "4. 周长、面积与简单几何图形",
            "elem_math_word_problems": "5. 鸡兔同笼与趣味应用题"
        },
        "elem_math_basic_operations": [],
        "elem_math_mixed_calc": ["elem_math_basic_operations"],
        "elem_math_fractions_decimals": ["elem_math_mixed_calc"],
        "elem_math_area_geometry": ["elem_math_basic_operations"],
        "elem_math_word_problems": ["elem_math_mixed_calc"]
    },

    # ── 小学 英语 (4大核心章节) ───────────────────────────────────────────────
    "小学 英语": {
        "__zh_names__": {
            "elem_eng_alphabet_phonics": "1. 26个字母与基础 Phonics 自然拼读",
            "elem_eng_basic_vocab": "2. 基础词汇(动物/颜色/家庭/日常)",
            "elem_eng_greetings_sentences": "3. 简单问候与自我介绍句型",
            "elem_eng_stories_dialogue": "4. 基础趣味绘本阅读与对话"
        },
        "elem_eng_alphabet_phonics": [],
        "elem_eng_basic_vocab": ["elem_eng_alphabet_phonics"],
        "elem_eng_greetings_sentences": ["elem_eng_basic_vocab"],
        "elem_eng_stories_dialogue": ["elem_eng_greetings_sentences"]
    },

    # ── 大学 高等数学 (8大核心章节) ───────────────────────────────────────────
    "大学 高等数学": {
        "__zh_names__": {
            "univ_math_limits_continuity": "1. 函数极限与连续性定理",
            "univ_math_single_var_calculus": "2. 一元函数微积分与导数应用",
            "univ_math_integrals": "3. 不定积分与定积分计算技巧",
            "univ_math_differential_eq": "4. 常微分方程与级数收敛性",
            "univ_math_spatial_vectors": "5. 向量代数与空间解析几何",
            "univ_math_multivariable_calculus": "6. 多元函数偏导数与全微分",
            "univ_math_multiple_integrals": "7. 二重积分与三重积分应用",
            "univ_math_line_surface_integrals": "8. 曲线积分与曲面积分(格林/高斯公式)"
        },
        "univ_math_limits_continuity": [],
        "univ_math_single_var_calculus": ["univ_math_limits_continuity"],
        "univ_math_integrals": ["univ_math_single_var_calculus"],
        "univ_math_differential_eq": ["univ_math_integrals"],
        "univ_math_spatial_vectors": ["univ_math_limits_continuity"],
        "univ_math_multivariable_calculus": ["univ_math_spatial_vectors"],
        "univ_math_multiple_integrals": ["univ_math_multivariable_calculus"],
        "univ_math_line_surface_integrals": ["univ_math_multiple_integrals"]
    },

    # ── 大学 / 职业 计算机科学 (8大核心章节) ──────────────────────────────────
    "计算机科学": {
        "__zh_names__": {
            "cs_programming_basics": "1. 变量、数据类型与控制流",
            "cs_linear_structures": "2. 线性数据结构(数组与链表)",
            "cs_trees_graphs": "3. 非线性结构(树与图论基础)",
            "cs_algorithms_search_sort": "4. 搜索与排序算法复杂度分析",
            "cs_oop_design_patterns": "5. 面向对象编程与 SOLID 设计原则",
            "cs_os_concurrency": "6. 操作系统内核与多线程并发",
            "cs_web_networking": "7. 计算机网络与 TCP/IP 协议族",
            "cs_database_architecture": "8. 数据库设计与 SQL/NoSQL 实战"
        },
        "cs_programming_basics": [],
        "cs_linear_structures": ["cs_programming_basics"],
        "cs_trees_graphs": ["cs_linear_structures"],
        "cs_algorithms_search_sort": ["cs_trees_graphs"],
        "cs_oop_design_patterns": ["cs_programming_basics"],
        "cs_os_concurrency": ["cs_linear_structures"],
        "cs_web_networking": ["cs_os_concurrency"],
        "cs_database_architecture": ["cs_oop_design_patterns"]
    },

    # ── 默认 / 通用（兜底） ───────────────────────────────────────────────────
    "数学": {
        "__zh_names__": {
            "junior_math_rational_numbers": "1. 有理数与数轴运算法则",
            "junior_math_polynomials_linear_eq": "2. 整式的加减与一元一次方程",
            "junior_math_system_linear_ineq": "3. 二元一次方程组与不等式组",
            "junior_math_lines_triangles": "4. 平行线、相交线与三角形全等",
            "junior_math_factoring_fractions": "5. 因式分解与分式方程",
            "junior_math_functions_intro": "6. 反比例函数与二次函数初步"
        },
        "junior_math_rational_numbers": [],
        "junior_math_polynomials_linear_eq": ["junior_math_rational_numbers"],
        "junior_math_system_linear_ineq": ["junior_math_polynomials_linear_eq"],
        "junior_math_lines_triangles": ["junior_math_rational_numbers"],
        "junior_math_factoring_fractions": ["junior_math_polynomials_linear_eq"],
        "junior_math_functions_intro": ["junior_math_system_linear_ineq"]
    },
    "英语": {
        "__zh_names__": {
            "junior_eng_parts_of_speech": "1. 八大词性与基本句型结构",
            "junior_eng_basic_tenses": "2. 一般现在时、过去时与进行时",
            "junior_eng_comparatives_modals": "3. 比较级、最高级与情态动词",
            "junior_eng_clauses_intro": "4. 宾语从句与定语从句基础",
            "junior_eng_cloze_reading": "5. 完形填空与日常对话阅读",
            "junior_eng_composition": "6. 情景对话与短文写作"
        },
        "junior_eng_parts_of_speech": [],
        "junior_eng_basic_tenses": ["junior_eng_parts_of_speech"],
        "junior_eng_comparatives_modals": ["junior_eng_basic_tenses"],
        "junior_eng_clauses_intro": ["junior_eng_parts_of_speech"],
        "junior_eng_cloze_reading": ["junior_eng_basic_tenses"],
        "junior_eng_composition": ["junior_eng_clauses_intro"]
    }
}


class LLMService:
    """Service to format prompts and execute chat completion API requests."""

    # Placeholder values that mean "not configured"
    PLACEHOLDER_KEYS = {
        "", 
        "your_deepseek_api_key_here", 
        "your_api_key_here",
        "sk-xxx",
    }

    async def generate_response(self, messages: list[dict], runtime_api_key: str = "") -> str:
        """
        Send a message sequence to the configured LLM API.

        If deepseek_api_key is not configured in settings, falls back to
        an offline mock responder to allow development/testing without API costs.
        """
        # Prefer runtime key (passed from frontend) over .env setting
        runtime = model_config_service.runtime
        api_key = runtime_api_key.strip() or runtime.llm_api_key.strip()

        # Offline Mock Fallback: triggered when key is absent or is a placeholder
        if not api_key or api_key in self.PLACEHOLDER_KEYS:
            logger.debug(
                "No DEEPSEEK_API_KEY set. Executing offline mock LLM response."
            )
            # Find the last user prompt to mock back matching context
            user_question = ""
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_question = msg["content"]
                    break

            # 智能离线模式：如果 user prompt 里包含教辅片段（CHAT/EXPLAIN 模板嵌入），
            # 直接抽取片段摘要作为回答，看起来像真在讲解
            context_block = ""
            for msg in messages:
                if msg["role"] == "user" and "未找到相关参考背景教辅资料" not in msg["content"]:
                    # 解析出 [Document N] 块
                    import re
                    docs = re.findall(
                        r"\[Document \d+\]: Title: ([^\n]+)\nContent: ((?:(?!\[Document).)+)",
                        msg["content"], re.DOTALL,
                    )
                    if docs:
                        context_block = docs[0][1][:600]
                        break

            if context_block:
                mock_text = (
                    f"你好！我是 EduMind AI 智能学习教练（离线模式）。\n\n"
                    f"我从教辅知识库里检索到与你问题高度相关的内容，先给你梳理要点：\n\n"
                    f"> {context_block}\n\n"
                    f"**教练建议**：\n"
                    f"1. 先理解上面片段里的关键概念与公式；\n"
                    f"2. 尝试用片段里的方法独立做 1~2 道基础题；\n"
                    f"3. 如果哪一步卡住，把你的思路发给我，我用启发式问题引导你，而不是直接给答案。\n\n"
                    f"---\n💡 配置 DEEPSEEK_API_KEY 后，我会基于以上教辅内容调用大模型给出更连贯、更个性化的讲解。"
                )
            else:
                mock_text = (
                    f"[Mock AI Coach Response]\n\n"
                    f"你好！我是 EduMind AI 智能学习教练。\n\n"
                    f"关于你的问题，我正在以\"离线模式\"为你解答。系统当前没有配置大模型 API 密钥 "
                    f"(DEEPSEEK_API_KEY)，但我从教辅知识库里暂时没找到匹配的片段。\n\n"
                    f"**教练建议**：学习是一个循序渐进的过程。请仔细阅读系统为你推荐的学习任务卡片，"
                    f"按照步骤先自学基本概念，再去挑战练习题。如果有困难，随时来找我探讨思路，"
                    f"我会一步步启发你，而不是直接抛给你答案。\n\n"
                    f"配置 API 密钥后，这里会呈现来自 DeepSeek 模型的真实教学指导。"
                )
            return mock_text

        # Online HTTP Call (OpenAI-compatible)
        url = f"{runtime.llm_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": runtime.llm_model,
            "messages": messages,
            "max_tokens": runtime.llm_max_tokens,
            "temperature": runtime.llm_temperature,
            "enable_thinking": runtime.llm_enable_thinking,
        }

        try:
            async with httpx.AsyncClient(timeout=runtime.llm_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(
                        f"LLM API returned status {response.status_code}: {response.text}"
                    )
                    raise ServiceUnavailableError("LLM Service API")

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content

        except Exception as exc:
            if isinstance(exc, ServiceUnavailableError):
                raise
            logger.error(f"Failed calling LLM API: {exc}", exc_info=True)
            raise ServiceUnavailableError("LLM Service Connection")

    async def chat(self, prompt: str, context: str, profile_summary: str, grade: str = "通用", runtime_api_key: str = "") -> str:
        """
        Engage in an AI coaching conversation with grade/stage adaptation.

        Hard-constraint RAG:
        - When `context` is empty / marked insufficient, use the NO_CONTEXT template
          to force a "资料不足" refusal and forbid fabrication.
        - Otherwise use the normal template with retrieved context.
        """
        # An empty/whitespace context, or the explicit "no material" marker,
        # both trigger the refusal branch.
        ctx_clean = (context or "").strip()
        insufficient = (not ctx_clean) or ctx_clean.startswith("（资料不足")

        if insufficient:
            user_content = CHAT_PROMPT_TEMPLATE_NO_CONTEXT.format(
                grade=grade,
                goal=profile_summary,
                mastery_summary=profile_summary,
                question=prompt,
            )
        else:
            user_content = CHAT_PROMPT_TEMPLATE.format(
                grade=grade,
                goal=profile_summary,
                mastery_summary=profile_summary,
                context=ctx_clean,
                question=prompt,
            )

        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return await self.generate_response(messages, runtime_api_key=runtime_api_key)

    async def explain(self, concept: str, context: str, subject: str = "通用", grade: str = "通用", runtime_api_key: str = "") -> str:
        """
        Generate a detailed topic explanation with grade/stage adaptation.

        Hard-constraint RAG: empty/insufficient context -> refusal branch.
        """
        ctx_clean = (context or "").strip()
        insufficient = (not ctx_clean) or ctx_clean.startswith("（资料不足")

        if insufficient:
            user_content = EXPLAIN_PROMPT_TEMPLATE_NO_CONTEXT.format(
                grade=grade,
                subject=subject,
                concept=concept,
            )
        else:
            user_content = EXPLAIN_PROMPT_TEMPLATE.format(
                grade=grade,
                subject=subject,
                context=ctx_clean,
                concept=concept,
            )

        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return await self.generate_response(messages, runtime_api_key=runtime_api_key)

    async def summarize_history(self, chat_history: str, runtime_api_key: str = "") -> str:
        """Summarize conversation history into a short title."""
        prompt = SUMMARIZE_PROMPT_TEMPLATE.format(history=chat_history)
        return await self.generate_response(
            [{"role": "user", "content": prompt}], runtime_api_key
        )

    async def generate_curriculum(self, subject: str, runtime_api_key: str = "") -> dict:
        """Dynamically generate a curriculum map (prerequisites graph) for a given subject using LLM."""
        # 1. Check exact match first (e.g., "高中 数学")
        if subject in PREDEFINED_CURRICULA:
            return PREDEFINED_CURRICULA[subject]

        # 2. Check fuzzy match
        for sub_key, cur in PREDEFINED_CURRICULA.items():
            if sub_key in subject or subject in sub_key:
                return cur

        prompt = GENERATE_CURRICULUM_PROMPT.format(subject=subject)
        response_text = await self.generate_response(
            [{"role": "user", "content": prompt}], runtime_api_key
        )
        
        # In offline/mock mode, return a fallback mock curriculum
        if "Mock AI Coach Response" in response_text or "No DEEPSEEK_API_KEY" in response_text:
            return {
                "__zh_names__": {
                    f"{subject}_basic": f"1. {subject}基础概念",
                    f"{subject}_intermediate": f"2. {subject}进阶应用",
                    f"{subject}_advanced": f"3. {subject}综合拔高"
                },
                f"{subject}_basic": [],
                f"{subject}_intermediate": [f"{subject}_basic"],
                f"{subject}_advanced": [f"{subject}_intermediate"]
            }

        # Parse JSON
        import json
        import re
        
        match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = response_text.strip()
            
        try:
            curriculum = json.loads(json_str)
            if "__zh_names__" not in curriculum:
                curriculum["__zh_names__"] = {}
            return curriculum
        except Exception as e:
            logger.error(f"Failed to parse LLM curriculum JSON: {e}\nResponse: {response_text}")
            return {
                "__zh_names__": {
                    "fallback_topic": "默认核心知识点"
                },
                "fallback_topic": []
            }

    async def summarize(self, conversation_history: list[dict]) -> str:
        """
        Summarize a dialog sequence.
        """
        if not settings.deepseek_api_key:
            # Quick mock summary
            return "关于学习内容与方法的探究"

        # Format history list into a readable string block
        history_text = ""
        for msg in conversation_history:
            role_name = "学生" if msg.get("role") == "user" else "教练"
            history_text += f"{role_name}: {msg.get('content')}\n"

        user_content = SUMMARIZE_PROMPT_TEMPLATE.format(history=history_text)

        messages = [
            {
                "role": "system",
                "content": "你是一个文本摘要助手。你的唯一目标是精简提炼对话主题。",
            },
            {"role": "user", "content": user_content},
        ]

        summary = await self.generate_response(messages)
        return summary.strip()

    async def generate_quiz(self, topic: str, runtime_api_key: str = "") -> str:
        """Generate a quiz question for a specific topic."""
        prompt = GENERATE_QUIZ_PROMPT.format(topic=topic)
        response_text = await self.generate_response(
            [{"role": "user", "content": prompt}], runtime_api_key
        )
        
        if "Mock AI Coach Response" in response_text or "No DEEPSEEK_API_KEY" in response_text:
            return f"（模拟测验）针对【{topic}】，请用自己的话解释一下它的核心概念是什么？"
            
        return response_text.strip()

    async def generate_structured_quiz(
        self,
        topic: str,
        subject: str,
        grade: str,
        leaf_label: str,
        runtime_api_key: str = "",
    ) -> dict | None:
        """
        Generate a single structured quiz question for a concept leaf.
        Returns a dict matching QuizQuestion fields, or None on failure/mock.
        """
        prompt = GENERATE_STRUCTURED_QUIZ_PROMPT.format(
            leaf_label=leaf_label, subject=subject or "通用", grade=grade or "通用"
        )
        response_text = await self.generate_response(
            [{"role": "user", "content": prompt}], runtime_api_key
        )

        if "Mock AI Coach Response" in response_text or "No DEEPSEEK_API_KEY" in response_text:
            return None

        import json as _json
        import re as _re
        cleaned = _re.sub(r"^```(?:json)?|```$", "", response_text.strip(), flags=_re.MULTILINE).strip()
        try:
            data = _json.loads(cleaned)
        except Exception as exc:
            logger.warning("generate_structured_quiz JSON parse failed: %s", exc)
            return None

        if not data.get("stem") or not data.get("question_type") or not data.get("correct_answer"):
            return None
        return data

    async def grade_answer(self, topic: str, question: str, answer: str, runtime_api_key: str = "") -> dict:
        """Grade a student's answer and return score and feedback."""
        prompt = GRADE_QUIZ_PROMPT.format(topic=topic, question=question, answer=answer)
        response_text = await self.generate_response(
            [{"role": "user", "content": prompt}], runtime_api_key
        )
        
        if "Mock AI Coach Response" in response_text or "No DEEPSEEK_API_KEY" in response_text:
            import random
            score = round(random.uniform(0.6, 1.0), 2)
            return {
                "score": score,
                "feedback": f"（模拟批改）你的回答收到了！系统随机给出了 {score} 分。干得不错，继续努力！"
            }
            
        import json
        import re
        match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = response_text.strip()
            
        try:
            result = json.loads(json_str)
            return result
        except Exception as e:
            logger.error(f"Failed to parse LLM grading JSON: {e}\nResponse: {response_text}")
            return {
                "score": 0.5,
                "feedback": "AI 批改出错，暂给一个鼓励分。你可以把思路再说详细点。"
            }

