"""
EduMind Objective Grading Engine

Pure-function rule-based scoring. LLM is NOT involved in scoring.

Supported types:
- single_choice    exact match            → 1.0 / 0.0
- multiple_choice  set ops + partial credit → 0.0 ~ 1.0
- true_false       exact match            → 1.0 / 0.0
- fill_blank       exact + fuzzy alias    → 1.0 / 0.7 / 0.0
- short_answer     keyword coverage       → tiered (0.0 / 0.4 / 0.7 / 1.0)

Each grader returns a dict:
{
    "score": 0.0~1.0,
    "is_correct": bool,
    "details": str,          # 简短的判分说明（前端展示）
}
"""

import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# 类型分派
# ─────────────────────────────────────────────────────────────────

def grade(question_type: str, correct_answer: dict, user_answer: dict) -> dict:
    """分派到对应判分器。"""
    graders = {
        "single_choice": _grade_single,
        "true_false": _grade_single,
        "multiple_choice": _grade_multiple,
        "fill_blank": _grade_fill,
        "short_answer": _grade_short,
    }
    grader = graders.get(question_type)
    if grader is None:
        logger.warning(f"Unknown question_type: {question_type}, returning 0")
        return {"score": 0.0, "is_correct": False, "details": "未知题型"}

    try:
        return grader(correct_answer, user_answer)
    except Exception as exc:
        logger.error(f"Grading failed for type={question_type}: {exc}", exc_info=True)
        return {"score": 0.0, "is_correct": False, "details": f"判分异常: {exc}"}


# ─────────────────────────────────────────────────────────────────────────
# 单选 / 判断：精确匹配
# ─────────────────────────────────────────────────────────────────

def _grade_single(correct: dict, user: dict) -> dict:
    expected = str(correct.get("answer", "")).strip().upper()
    got = str(user.get("answer", "")).strip().upper()
    if not expected:
        return {"score": 0.0, "is_correct": False, "details": "题目缺少标准答案"}

    is_correct = got == expected
    return {
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "details": f"正确答案 {expected}，你的答案 {got}"
                   if not is_correct else f"回答正确 ({expected})",
    }


# ─────────────────────────────────────────────────────────────────────────
# 多选：部分给分（漏选按比例，错选直接 0）
# ─────────────────────────────────────────────────────────────────

def _grade_multiple(correct: dict, user: dict) -> dict:
    correct_set = set(correct.get("answers", []))
    user_set = set(user.get("answers", []))

    if not correct_set:
        return {"score": 0.0, "is_correct": False, "details": "题目缺少标准答案"}

    only_wrong = user_set - correct_set
    intersect = correct_set & user_set
    missing = correct_set - user_set

    if only_wrong:
        # 选了错误选项 → 0 分
        return {
            "score": 0.0,
            "is_correct": False,
            "details": f"包含错误选项 {sorted(only_wrong)}，不得分",
        }

    if not user_set:
        return {"score": 0.0, "is_correct": False, "details": "未作答"}

    ratio = len(intersect) / len(correct_set)
    is_correct = ratio == 1.0
    if is_correct:
        details = f"完全正确 ({', '.join(sorted(correct_set))})"
    else:
        details = f"漏选 {sorted(missing)}，得 {round(ratio*100)}% 分数"

    return {"score": ratio, "is_correct": is_correct, "details": details}


# ─────────────────────────────────────────────────────────────────────────
# 填空：精确匹配 + 别名模糊匹配
# ─────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return "".join(str(text).lower().split()).replace(",", "").replace("，", "")


def _grade_fill(correct: dict, user: dict) -> dict:
    expected_raw = str(correct.get("answer", "")).strip()
    aliases = correct.get("aliases", []) or []
    candidates = [expected_raw] + [str(a).strip() for a in aliases]

    got = str(user.get("text", user.get("answer", ""))).strip()
    if not got:
        return {"score": 0.0, "is_correct": False, "details": "未作答"}

    # 1) 精确匹配（去除空白与标点）
    got_n = _normalize(got)
    for cand in candidates:
        if got_n == _normalize(cand):
            return {"score": 1.0, "is_correct": True, "details": f"回答正确 ({cand})"}

    # 2) 模糊匹配（相似度 ≥ 0.85）
    best_ratio = 0.0
    best_cand = ""
    for cand in candidates:
        r = SequenceMatcher(None, got_n, _normalize(cand)).ratio()
        if r > best_ratio:
            best_ratio = r
            best_cand = cand

    if best_ratio >= 0.85:
        return {
            "score": 0.7,
            "is_correct": False,
            "details": f"接近正确答案「{best_cand}」（相似度 {round(best_ratio*100)}%）",
        }

    return {
        "score": 0.0,
        "is_correct": False,
        "details": f"答案偏差较大，正确答案：{expected_raw}",
    }


# ─────────────────────────────────────────────────────────────────────────
# 简答：关键词命中（覆盖率分档）
# ─────────────────────────────────────────────────────────────────

def _grade_short(correct: dict, user: dict) -> dict:
    keywords = correct.get("keywords", []) or []
    if not keywords:
        # 无关键词时按文本长度给鼓励分
        text = str(user.get("text", "")).strip()
        if len(text) >= 30:
            return {"score": 0.7, "is_correct": False, "details": "回答较完整，但缺少评分依据"}
        return {"score": 0.0, "is_correct": False, "details": "回答过短"}

    text = str(user.get("text", "")).strip()
    if not text:
        return {"score": 0.0, "is_correct": False, "details": "未作答"}

    text_lower = text.lower()
    hit_count = sum(1 for kw in keywords if str(kw).lower() in text_lower)
    ratio = hit_count / len(keywords)

    if ratio >= 1.0:
        return {
            "score": 1.0, "is_correct": True,
            "details": f"覆盖全部 {len(keywords)} 个关键点",
        }
    if ratio >= 0.6:
        return {
            "score": 0.7, "is_correct": False,
            "details": f"命中 {hit_count}/{len(keywords)} 个关键点（{round(ratio*100)}%）",
        }
    if ratio >= 0.3:
        return {
            "score": 0.4, "is_correct": False,
            "details": f"命中 {hit_count}/{len(keywords)} 个关键点（{round(ratio*100)}%）",
        }
    return {
        "score": 0.0, "is_correct": False,
        "details": f"关键点命中过低（{hit_count}/{len(keywords)}）",
    }