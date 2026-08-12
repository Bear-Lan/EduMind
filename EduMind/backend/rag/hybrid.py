"""
Hybrid recall: vector search + precise keyword / exact-term search.

Improves recall for:
  - problem numbers (题1 / 例2 / 第3题 / Ex.4)
  - section refs (§1.2 / 1.2.3)
  - formula & theorem names (勾股定理 / 韦达定理 / Vieta)
  - proper nouns & symbolic tokens (Newton / Δ / sin2θ)
"""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import LearningResource
from rag.filters import resource_matches_scope

# 题号 / 例题
_PROBLEM_NO = re.compile(
    r"(?:"
    r"第\s*[0-9一二三四五六七八九十百]+\s*题"
    r"|题\s*[0-9]+(?:\s*[\.．、]\s*[0-9]+)?"
    r"|例\s*[0-9]+(?:\s*[\.．、]\s*[0-9]+)?"
    r"|练习\s*[0-9]+"
    r"|习题\s*[0-9]+"
    r"|(?:Ex(?:ercise)?|Problem|Q)\s*\.?\s*[0-9]+(?:\.[0-9]+)?"
    r")",
    re.IGNORECASE,
)

# 章节 / 小节编号
_SECTION_NO = re.compile(
    r"(?:"
    r"§\s*[0-9]+(?:\.[0-9]+)*"
    r"|第\s*[0-9一二三四五六七八九十百]+\s*[章节部篇]"
    r"|(?<![A-Za-z])[0-9]+(?:\.[0-9]+){1,3}(?![0-9])"
    r")"
)

# 公式 / 定理 / 法则专名（中文）— 非贪婪，避免吃掉「请讲」前缀
_CN_FORMULA = re.compile(
    r"(?:"
    r"[\u4e00-\u9fff]{1,8}?(?:定理|公式|法则|定律|不等式|方程|引理|推论|公理|准则|原理|恒等式|二项式|多项式)"
    r"|[\u4e00-\u9fff]{2,6}(?:公式|定理)"
    r")"
)

# 英文专名 / 公式名（含常见数学命名）
_EN_PROPER = re.compile(
    r"(?:"
    r"[A-Z][a-z]+(?:'[sS])?(?:\s+[A-Z][a-z]+)*"  # Newton / Vieta's Formulas
    r"|(?:sin|cos|tan|cot|sec|csc|log|ln|lim|exp|max|min|gcd|lcm)\w*"
    r"|(?:Pythagorean|Vieta|Newton|Euler|Bayes|Lagrange|Fourier|Taylor|Cauchy|Stokes)\w*"
    r")",
)

# 符号 / 短精确串
_SYMBOLIC = re.compile(
    r"(?:"
    r"[Δδ∑∫∏√∞≈≠≤≥∈∉⊆∪∩⊥∥]"
    r"|\\frac\{[^}]+\}\{[^}]+\}"
    r"|[a-zA-Z]_\{?[0-9]+\}?"
    r"|[0-9]+[a-zA-Z]+"  # 2x, 3sin
    r")"
)


_FLUFF_CN = re.compile(
    r"(请讲|请你|讲解|解释|帮我|参考|一下|什么是|怎么|如何|告诉|说说|看看)"
)
_LEADING_NOISE = re.compile(r"^[用的是在对把将与和及到给求证证明]+")
_FORMULA_HEAD_NOISE = re.compile(r"^[题例第练习习题用的是在对把将与和及到给]+")
_FORMULA_SUFFIXES = (
    "恒等式",
    "不等式",
    "二项式",
    "多项式",
    "定理",
    "公式",
    "法则",
    "定律",
    "方程",
    "引理",
    "推论",
    "公理",
    "准则",
    "原理",
)


def _tighten_cn_formula(term: str) -> str:
    """Shrink noisy spans like 题用牛顿二项式 → 牛顿二项式."""
    term = (term or "").strip()
    if not term:
        return term
    for suf in _FORMULA_SUFFIXES:
        if not term.endswith(suf):
            continue
        head = _FORMULA_HEAD_NOISE.sub("", term[: -len(suf)])
        if 1 <= len(head) <= 8:
            return head + suf
    return term


_EN_STOP = frozenset(
    {
        "explain",
        "please",
        "what",
        "how",
        "why",
        "when",
        "where",
        "which",
        "about",
        "with",
        "from",
        "this",
        "that",
        "these",
        "those",
        "formula",
        "formulas",
        "theorem",
        "theorems",
        "problem",
        "exercise",
        "question",
        "example",
        "chapter",
        "section",
    }
)


def extract_precise_terms(query: str, *, max_terms: int = 12) -> list[str]:
    """
    Pull high-precision lexical anchors from the user query.
    Prefers theorem/formula names, problem numbers, section refs.
    """
    q = (query or "").strip()
    if not q:
        return []

    priority: list[tuple[int, str]] = []  # (priority, term) lower=better

    def add(prio: int, term: str) -> None:
        term = _FLUFF_CN.sub("", (term or "").strip()).strip()
        term = _LEADING_NOISE.sub("", term).strip()
        if len(term) < 1:
            return
        priority.append((prio, term))

    covered: list[tuple[int, int]] = []

    def mark_span(start: int, end: int) -> None:
        covered.append((start, end))

    def overlaps(start: int, end: int) -> bool:
        return any(not (end <= a or start >= b) for a, b in covered)

    for m in _PROBLEM_NO.finditer(q):
        add(0, m.group(0))
        mark_span(*m.span())
    for m in _SECTION_NO.finditer(q):
        add(0, m.group(0))
        mark_span(*m.span())
    for m in _CN_FORMULA.finditer(q):
        add(1, _tighten_cn_formula(m.group(0)))
        mark_span(*m.span())
    for m in _EN_PROPER.finditer(q):
        if overlaps(*m.span()):
            continue
        raw = m.group(0)
        parts = raw.split()
        while parts and parts[0].casefold() in _EN_STOP:
            parts.pop(0)
        if not parts or (len(parts) == 1 and parts[0].casefold() in _EN_STOP):
            continue
        term = " ".join(parts)
        if term.casefold() in _EN_STOP:
            continue
        add(1, term)
        mark_span(*m.span())
    for m in _SYMBOLIC.finditer(q):
        if overlaps(*m.span()):
            continue
        add(2, m.group(0))
        mark_span(*m.span())

    for m in re.finditer(r"[\u4e00-\u9fff]{3,8}", q):
        if overlaps(*m.span()):
            continue
        t = m.group(0)
        if _FLUFF_CN.search(t):
            cleaned = _FLUFF_CN.sub("", t).strip()
            if len(cleaned) >= 2:
                add(3, cleaned)
            continue
        add(4, t)

    # Dedup: best priority first; for overlapping phrases prefer shorter clean names
    # (勾股定理 over 请讲勾股定理) unless token is a problem/section ref.
    priority.sort(key=lambda x: (x[0], len(x[1]), x[1].casefold()))
    out: list[str] = []
    seen: set[str] = set()
    for _, t in priority:
        key = t.casefold()
        if key in seen:
            continue
        precise = bool(_PROBLEM_NO.fullmatch(t) or _SECTION_NO.fullmatch(t))
        if not precise:
            # Drop longer noisy supersets already kept
            if any(key != s and s in key for s in seen):
                continue
            # Replace longer kept terms that contain this cleaner term
            drop = {s for s in seen if key != s and key in s}
            if drop:
                seen -= drop
                out = [x for x in out if x.casefold() not in drop]
        seen.add(key)
        out.append(t)
        if len(out) >= max_terms:
            break
    return out


def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    *,
    k: int = 60,
    weights: list[float] | None = None,
) -> list[tuple[int, float]]:
    """
    RRF over resource IDs.
    ranked_lists[i] = ordered resource ids from channel i (best first).
    Returns [(resource_id, rrf_score)] sorted desc.
    """
    if not ranked_lists:
        return []
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    while len(weights) < len(ranked_lists):
        weights.append(1.0)

    scores: dict[int, float] = defaultdict(float)
    for w, ids in zip(weights, ranked_lists):
        for rank, rid in enumerate(ids):
            if rid is None:
                continue
            scores[int(rid)] += float(w) * (1.0 / (k + rank + 1))

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


async def keyword_search(
    db: AsyncSession,
    query: str,
    *,
    limit: int = 20,
    subject_key: str | None = None,
    stage: str | None = None,
    require_stage: bool = False,
) -> list[tuple[LearningResource, float]]:
    """
    SQL keyword / exact-term search over title/content/chapter/section/topic/source.

    Score ∈ (0, 1]: longer exact hits in title/chapter weigh more than body hits.
    """
    terms = extract_precise_terms(query)
    if not terms:
        # Fallback: use 2+ char tokens from query as soft keywords
        terms = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_\-]{2,}", query or "")
        terms = terms[:6]
    if not terms:
        return []

    clauses = []
    for term in terms:
        # Escape LIKE wildcards so user input cannot broaden matches
        safe = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{safe}%"
        clauses.extend(
            [
                LearningResource.title.ilike(like, escape="\\"),
                LearningResource.content.ilike(like, escape="\\"),
                LearningResource.chapter.ilike(like, escape="\\"),
                LearningResource.section.ilike(like, escape="\\"),
                LearningResource.topic.ilike(like, escape="\\"),
                LearningResource.source.ilike(like, escape="\\"),
                LearningResource.parent_doc.ilike(like, escape="\\"),
            ]
        )

    rows = (
        await db.scalars(
            select(LearningResource).where(or_(*clauses)).limit(max(limit * 4, 40))
        )
    ).all()

    scored: list[tuple[LearningResource, float]] = []
    for res in rows:
        if not resource_matches_scope(
            res.subject, subject_key, stage, require_stage=require_stage
        ):
            continue
        score = _keyword_hit_score(res, terms)
        if score > 0:
            scored.append((res, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def _keyword_hit_score(res: LearningResource, terms: list[str]) -> float:
    title = (res.title or "").casefold()
    parent = (res.parent_doc or "").casefold()
    chapter = (res.chapter or "").casefold()
    section = (res.section or "").casefold()
    topic = (res.topic or "").casefold()
    source = (res.source or "").casefold()
    content = (res.content or "").casefold()

    score = 0.0
    for term in terms:
        t = term.casefold()
        if not t:
            continue
        # Exact-ish weights
        if t in title or t in parent:
            score += 1.0
        elif t in chapter or t in section:
            score += 0.85
        elif t in topic or t in source:
            score += 0.6
        elif t in content:
            # density: more occurrences → slightly higher, capped
            occ = content.count(t)
            score += min(0.55, 0.25 + 0.05 * occ)
        # Extra boost for problem / section number exactness
        if _PROBLEM_NO.fullmatch(term) or _SECTION_NO.fullmatch(term):
            blob = f"{title} {chapter} {section} {content}"
            if t in blob:
                score += 0.35

    # Normalize to (0, 1]
    return max(0.0, min(1.0, score / max(1.0, 0.8 * len(terms))))
