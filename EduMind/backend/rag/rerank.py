"""
RAG rerankers: lexical overlap (+ optional future cross-encoder hook).

Pipeline expectation:
  vector recall Top-N  →  rerank  →  keep Top-K
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from models.resource import LearningResource

_TOKEN_RE = re.compile(
    r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_\-]{1,}|[0-9]+(?:\.[0-9]+)?"
)
# Split long CN runs so question fluff does not become one giant token
_CN_SPLIT = re.compile(
    r"(怎么|怎样|如何|什么|请问|一下|讲解|解释|告诉我|告诉|帮我|可以吗|可以|吗|呢|啊|呀|么|求一下)"
)
_CN_STOP_BIGRAMS = {
    "怎么",
    "怎样",
    "如何",
    "什么",
    "请问",
    "一下",
    "讲解",
    "解释",
    "告诉",
    "帮我",
    "可以",
    "吗呢",
    "啊呀",
}


def tokenize(text: str) -> list[str]:
    """Lightweight CN/EN tokenizer with stopword-aware Chinese splits."""
    raw = (text or "").casefold()
    toks: list[str] = []
    for m in _TOKEN_RE.finditer(raw):
        t = m.group(0)
        if not t:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{2,}", t):
            parts = [p for p in _CN_SPLIT.split(t) if p and not _CN_SPLIT.fullmatch(p)]
            if not parts:
                parts = [t]
            for part in parts:
                if len(part) < 2:
                    continue
                toks.append(part)
                if len(part) > 2:
                    for i in range(len(part) - 1):
                        bg = part[i : i + 2]
                        if bg not in _CN_STOP_BIGRAMS:
                            toks.append(bg)
        else:
            toks.append(t)
    return toks


def lexical_overlap_score(query: str, document: str) -> float:
    """
    Coverage-oriented overlap in [0, 1].

    Uses contentful query terms (length-weighted) against the document token set
    and raw substring presence.
    """
    q_list = tokenize(query)
    if not q_list:
        return 0.0
    d_text = (document or "").casefold()
    d_toks = set(tokenize(d_text))

    weighted_hit = 0.0
    weighted_total = 0.0
    for term in set(q_list):
        w = min(3.0, max(1.0, len(term) / 2.0))
        weighted_total += w
        hit = term in d_toks or (len(term) >= 2 and term in d_text)
        if hit:
            weighted_hit += w

    if weighted_total <= 0:
        return 0.0
    coverage = weighted_hit / weighted_total

    q_set = set(q_list)
    inter = len(q_set & d_toks)
    jaccard = inter / max(len(q_set | d_toks), 1)
    return max(0.0, min(1.0, 0.8 * coverage + 0.2 * jaccard))


def _field_text(res: LearningResource) -> str:
    parts = [
        res.title or "",
        res.parent_doc or "",
        res.chapter or "",
        res.section or "",
        res.topic or "",
        res.subject or "",
        res.content or "",
    ]
    return "\n".join(p for p in parts if p)


@dataclass
class RankedHit:
    resource: LearningResource
    vector_score: float
    lexical_score: float
    final_score: float


def rerank_keyword_overlap(
    query: str,
    items: list[tuple[LearningResource, float]],
    *,
    top_k: int = 3,
    vector_weight: float = 0.55,
    lexical_weight: float | None = None,
    title_bonus: float = 0.12,
) -> list[tuple[LearningResource, float]]:
    """
    Fuse vector similarity with keyword overlap; return Top-K.

    final = w_v * vector + w_l * lexical (+ title/topic hit bonus)
    Returned score is the fused final score (for citations / thresholding).
    """
    if not items:
        return []

    w_v = max(0.0, min(1.0, float(vector_weight)))
    w_l = (1.0 - w_v) if lexical_weight is None else max(0.0, float(lexical_weight))
    s = w_v + w_l
    if s <= 0:
        w_v, w_l = 0.55, 0.45
    else:
        w_v, w_l = w_v / s, w_l / s

    q_toks = {t for t in tokenize(query) if len(t) >= 2}
    ranked: list[RankedHit] = []
    for res, vec in items:
        doc = _field_text(res)
        lex = lexical_overlap_score(query, doc)
        bonus = 0.0
        title_blob = f"{res.title or ''} {res.parent_doc or ''} {res.topic or ''}".casefold()
        if q_toks and any(t in title_blob for t in q_toks):
            bonus = title_bonus
        final = max(0.0, min(1.0, w_v * float(vec) + w_l * lex + bonus))
        ranked.append(
            RankedHit(
                resource=res,
                vector_score=float(vec),
                lexical_score=lex,
                final_score=final,
            )
        )

    ranked.sort(
        key=lambda h: (h.final_score, h.lexical_score, h.vector_score),
        reverse=True,
    )
    return [(h.resource, h.final_score) for h in ranked[: max(1, top_k)]]
