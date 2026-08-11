"""
Build a chapter-scoped concept tree from textbook LearningResource rows.

Tree shape:
  chapter (root)
    └── resource title (branch, from 教辅篇目)
          └── key point (leaf)
                ├── 知识点精讲 (virtual child, opens lecture)
                └── 例题练习   (virtual child, opens quiz, slot 1 & 2)
"""

from __future__ import annotations

import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import LearningResource
from services.concept_mastery import (
    annotate_tree_levels,
    next_quiz_slot,
    progress_to_level,
    stable_leaf_id,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[。；;！？\n])")


def extract_key_points(content: str, limit: int = 6) -> list[str]:
    if not content or not content.strip():
        return []

    raw_parts = _SENTENCE_SPLIT.split(content)
    points: list[str] = []
    seen: set[str] = set()

    for part in raw_parts:
        text = re.sub(r"\s+", " ", part).strip(" \t\r\n-•·、")
        if len(text) < 8:
            continue
        if len(text) > 72:
            text = text[:70].rstrip() + "…"
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        points.append(text)
        if len(points) >= limit:
            break

    return points


def _leaf_virtual_children(leaf_id: str, progress: dict | None) -> list[dict]:
    """
    Two clickable virtual children: lecture + quiz.

    `progress` is the raw per-leaf dict {lecture, quiz1:{correct}, quiz2:{correct}}.
    The quiz child carries `next_slot` (1/2/None) so the frontend can open the
    first not-yet-correct slot — this is what lets a leaf actually reach L3.
    """
    p = progress or {}
    lecture_done = bool(p.get("lecture"))
    quiz1_correct = bool(p.get("quiz1", {}).get("correct"))
    quiz2_correct = bool(p.get("quiz2", {}).get("correct"))
    quiz_done = quiz1_correct and quiz2_correct
    next_slot = None if quiz_done else next_quiz_slot(p)
    return [
        {
            "id": f"{leaf_id}::lecture",
            "label": "知识点精讲",
            "leaf": True,
            "virtual": "lecture",
            "leaf_id": leaf_id,
            "level": 1 if lecture_done else 0,
            "done": lecture_done,
        },
        {
            "id": f"{leaf_id}::quiz",
            "label": "例题练习",
            "leaf": True,
            "virtual": "quiz",
            "leaf_id": leaf_id,
            "level": 1 if quiz_done else 0,
            "done": quiz_done,
            "next_slot": next_slot,
        },
    ]


async def build_concept_tree_for_topic(
    db: AsyncSession,
    topic: str,
    topic_label: str | None = None,
    max_branches: int = 4,
    max_leaves_per_branch: int = 6,
    leaf_levels: dict[str, int] | None = None,
    leaf_progress: dict[str, dict] | None = None,
) -> dict:
    topic = (topic or "").strip()
    label = (topic_label or topic).strip() or topic

    empty = {
        "topic": topic,
        "label": label,
        "children": [],
        "resource_count": 0,
        "level": 0,
    }
    if not topic:
        return empty

    rows = (
        await db.scalars(
            select(LearningResource)
            .where(LearningResource.topic == topic)
            .order_by(LearningResource.id.asc())
            .limit(max_branches)
        )
    ).all()

    # Single source of truth: prefer raw per-leaf progress; derive levels from it.
    # Fall back to leaf_levels (legacy) when progress not supplied.
    if leaf_progress is not None:
        levels = {lid: progress_to_level(p) for lid, p in leaf_progress.items()}
    else:
        levels = leaf_levels or {}
    progress_map = leaf_progress or {}

    children = []
    for res in rows:
        leaves = extract_key_points(res.content or "", limit=max_leaves_per_branch)
        if not leaves:
            continue
        leaf_nodes = []
        for point in leaves:
            lid = stable_leaf_id(res.id, point)
            lvl = int(levels.get(lid, 0))
            prog = progress_map.get(lid) or {}
            leaf_nodes.append(
                {
                    "id": lid,
                    "label": point,
                    "leaf": True,
                    "level": lvl,
                    "resource_id": res.id,
                    "progress": prog,
                    "children": _leaf_virtual_children(lid, prog),
                }
            )
        children.append(
            {
                "id": f"res-{res.id}",
                "label": res.title,
                "source": res.source,
                "children": leaf_nodes,
            }
        )

    tree = {
        "topic": topic,
        "label": label,
        "children": children,
        "resource_count": len(rows),
    }
    return annotate_tree_levels(tree, levels)
