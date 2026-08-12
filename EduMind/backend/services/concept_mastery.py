"""
Concept-leaf mastery for chapter skill trees.

Per-leaf progress model:
  { lecture: bool, quiz1: {qid, correct}, quiz2: {qid, correct} }
Leaf level (0-3) = (lecture?1:0) + (quiz1.correct?1:0) + (quiz2.correct?1:0)
Parent / branch level = round(mean of children).
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from models.quiz import QuizQuestion
from student_profile import student_profile_service

logger = logging.getLogger(__name__)

MAX_LEAF_LEVEL = 3
PROGRESS_KEY = "concept_leaf_progress"


def stable_leaf_id(resource_id: int, point_text: str) -> str:
    digest = hashlib.md5(point_text.encode("utf-8")).hexdigest()[:10]
    return f"leaf-{resource_id}-{digest}"


def clamp_level(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(MAX_LEAF_LEVEL, n))


def _empty_progress() -> dict:
    return {"lecture": False, "quiz1": {"qid": None, "correct": False}, "quiz2": {"qid": None, "correct": False}}


def _progress_to_level(prog: dict) -> int:
    if not prog:
        return 0
    lvl = 0
    if prog.get("lecture"):
        lvl += 1
    q1 = prog.get("quiz1") if isinstance(prog.get("quiz1"), dict) else {}
    q2 = prog.get("quiz2") if isinstance(prog.get("quiz2"), dict) else {}
    if q1.get("correct"):
        lvl += 1
    if q2.get("correct"):
        lvl += 1
    return clamp_level(lvl)


def progress_to_level(prog: dict | None) -> int:
    """Public helper: raw per-leaf progress dict → mastery level 0-3."""
    return _progress_to_level(prog or {})


def next_quiz_slot(prog: dict | None) -> int | None:
    """First quiz slot (1 or 2) not yet answered correctly; None if both done."""
    p = prog or {}
    q1 = p.get("quiz1") if isinstance(p.get("quiz1"), dict) else {}
    q2 = p.get("quiz2") if isinstance(p.get("quiz2"), dict) else {}
    if not q1.get("correct"):
        return 1
    if not q2.get("correct"):
        return 2
    return None


def get_leaf_progress(profile) -> dict[str, dict]:
    prefs = dict(profile.learning_preferences or {})
    raw = prefs.get(PROGRESS_KEY) or {}
    out: dict[str, dict] = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            # Normalize nested quiz slots so callers can safely .get("correct")
            q1 = v.get("quiz1") if isinstance(v.get("quiz1"), dict) else {"qid": None, "correct": False}
            q2 = v.get("quiz2") if isinstance(v.get("quiz2"), dict) else {"qid": None, "correct": False}
            out[str(k)] = {
                "lecture": bool(v.get("lecture")),
                "quiz1": {"qid": q1.get("qid"), "correct": bool(q1.get("correct"))},
                "quiz2": {"qid": q2.get("qid"), "correct": bool(q2.get("correct"))},
            }
        elif isinstance(v, (int, float)):
            # Legacy: stored bare level int → approximate progress
            lvl = clamp_level(v)
            out[str(k)] = {
                "lecture": lvl >= 1,
                "quiz1": {"qid": None, "correct": lvl >= 2},
                "quiz2": {"qid": None, "correct": lvl >= 3},
            }
        # ignore corrupt entries
    return out


def get_leaf_levels(profile) -> dict[str, int]:
    """Derive leaf levels from progress (single source of truth)."""
    progress = get_leaf_progress(profile)
    return {lid: _progress_to_level(p) for lid, p in progress.items()}


async def _ensure_profile(db: AsyncSession, student_id: int):
    profile = await student_profile_service.get_profile(db, student_id)
    prefs = dict(profile.learning_preferences or {})
    # Reuse the same normalizer so legacy/corrupt entries don't crash writes
    progress = get_leaf_progress(profile)
    return profile, prefs, progress


async def mark_lecture_done(db: AsyncSession, student_id: int, leaf_id: str) -> dict:
    profile, prefs, progress = await _ensure_profile(db, student_id)
    lid = str(leaf_id)
    prog = progress.get(lid) or _empty_progress()
    prog["lecture"] = True
    progress[lid] = prog
    prefs[PROGRESS_KEY] = progress
    profile.learning_preferences = prefs
    flag_modified(profile, "learning_preferences")
    await db.flush()
    return {"leaf_id": lid, "level": _progress_to_level(prog), "progress": prog}


async def record_quiz_result(
    db: AsyncSession,
    student_id: int,
    leaf_id: str,
    slot: int,
    question_id: int,
    is_correct: bool,
) -> dict:
    if slot not in (1, 2):
        raise ValueError("slot must be 1 or 2")
    profile, prefs, progress = await _ensure_profile(db, student_id)
    lid = str(leaf_id)
    prog = progress.get(lid) or _empty_progress()
    key = f"quiz{slot}"
    prog[key] = {"qid": question_id, "correct": bool(is_correct)}
    progress[lid] = prog
    prefs[PROGRESS_KEY] = progress
    profile.learning_preferences = prefs
    flag_modified(profile, "learning_preferences")
    await db.flush()
    return {"leaf_id": lid, "level": _progress_to_level(prog), "progress": prog}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "")).casefold()


def match_leaves_for_question(
    question: QuizQuestion,
    leaves: list[dict],
) -> list[str]:
    if not leaves:
        return []

    tags = [str(t).strip() for t in (question.knowledge_tags or []) if str(t).strip()]
    stem_n = _normalize(question.stem or "")
    matched: list[str] = []
    seen: set[str] = set()

    def add(leaf_id: str) -> None:
        if leaf_id and leaf_id not in seen:
            seen.add(leaf_id)
            matched.append(leaf_id)

    if tags:
        for leaf in leaves:
            lid = leaf.get("id") or ""
            label_n = _normalize(leaf.get("label") or "")
            for tag in tags:
                tag_n = _normalize(tag)
                if not tag_n:
                    continue
                if tag == lid or tag_n == _normalize(lid):
                    add(lid)
                elif len(tag_n) >= 2 and (tag_n in label_n or label_n in tag_n):
                    add(lid)

    if matched:
        return matched

    for leaf in leaves:
        label = (leaf.get("label") or "").strip()
        label_n = _normalize(label)
        if len(label_n) < 4 or not stem_n:
            continue
        core = label_n[:16] if len(label_n) >= 8 else label_n
        if core and core in stem_n:
            add(leaf["id"])
            continue
        tokens = re.findall(r"[\u4e00-\u9fff]{4,}|[a-zA-Z0-9]{4,}", label)
        hit = sum(1 for t in tokens if _normalize(t) in stem_n)
        if hit >= 1 and len(tokens) <= 3:
            add(leaf["id"])
        elif hit >= 2:
            add(leaf["id"])

    return matched


def collect_leaves(tree: dict) -> list[dict]:
    leaves: list[dict] = []

    def walk(node: dict) -> None:
        kids = node.get("children") or []
        if node.get("leaf") or not kids:
            if node.get("id") and node.get("leaf"):
                leaves.append(node)
            return
        for child in kids:
            walk(child)

    for branch in tree.get("children") or []:
        walk(branch)
    return leaves


def annotate_tree_levels(tree: dict, leaf_levels: dict[str, int]) -> dict:
    """Attach `level` on every node. Leaves read from storage; parents = round(mean(children))."""

    def annotate(node: dict) -> int:
        kids = node.get("children") or []
        if node.get("leaf") or not kids:
            level = clamp_level(leaf_levels.get(node.get("id") or "", 0))
            node["level"] = level
            return level

        child_levels = [annotate(child) for child in kids]
        if not child_levels:
            level = 0
        else:
            level = int(round(sum(child_levels) / len(child_levels)))
            level = clamp_level(level)
        node["level"] = level
        return level

    root = dict(tree)
    root_children = [dict(c) for c in (tree.get("children") or [])]
    copied_children = []
    for branch in root_children:
        b = dict(branch)
        b["children"] = [dict(leaf) for leaf in (branch.get("children") or [])]
        copied_children.append(b)
    root["children"] = copied_children

    if not root["children"]:
        root["level"] = 0
        return root

    child_levels = [annotate(branch) for branch in root["children"]]
    root["level"] = clamp_level(int(round(sum(child_levels) / len(child_levels))))
    return root


# Backward-compat: keep the old function name working for chapter-level quiz submit.
async def apply_correct_answer_to_concept_tree(
    db: AsyncSession,
    student_id: int,
    question: QuizQuestion,
    leaves: list[dict],
) -> dict:
    """Legacy: chapter quiz correct → bump matched leaf's quiz1 slot (if empty)."""
    matched = match_leaves_for_question(question, leaves)
    out: dict = {}
    for lid in matched:
        prog = (await _ensure_profile(db, student_id))[2].get(lid) or _empty_progress()
        if not prog.get("quiz1", {}).get("qid"):
            res = await record_quiz_result(db, student_id, lid, 1, question.id, True)
            out[lid] = res["level"]
    return out
