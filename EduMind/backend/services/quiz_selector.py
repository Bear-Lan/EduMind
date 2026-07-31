"""
EduMind Quiz Selector

根据学生 mastery 自适应选题（1~5 难度）。
"""

import logging
import random
from typing import Iterable

from sqlalchemy import select, not_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from models.quiz import QuizQuestion, QuizAttempt

logger = logging.getLogger(__name__)


def _mastery_to_target_level(mastery: float) -> int:
    """mastery ∈ [0,1] → 目标难度 1~5。"""
    if mastery < 0.4:
        return 1
    if mastery < 0.7:
        return 2
    if mastery < 0.85:
        return 3
    return 4


async def pick_question(
    db: AsyncSession,
    *,
    subject: str,
    topic: str,
    student_id: int,
    mastery: float = 0.0,
    exclude_recent: int = 5,
) -> QuizQuestion | None:
    """
    自适应选题。

    难度区间：target_level ± 1
    排除最近 `exclude_recent` 道做过的题
    无候选时返回 None
    """
    target = _mastery_to_target_level(mastery)

    # 最近做过的题 id
    recent_qids: Iterable[int] = set()
    if exclude_recent > 0:
        recent_rows = await db.execute(
            select(QuizAttempt.question_id)
            .where(QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.created_at.desc())
            .limit(exclude_recent)
        )
        recent_qids = {row[0] for row in recent_rows.all()}

    # 主查询：subject + topic + 难度区间 + 排除最近
    stmt = (
        select(QuizQuestion)
        .where(
            QuizQuestion.subject == subject,
            QuizQuestion.topic == topic,
            QuizQuestion.difficulty.between(max(1, target - 1), min(5, target + 1)),
            not_(QuizQuestion.id.in_(recent_qids)) if recent_qids else True,
        )
    )

    rows = (await db.execute(stmt)).scalars().all()
    if rows:
        return random.choice(rows)

    # 兜底：放宽难度区间
    fallback = (
        await db.execute(
            select(QuizQuestion).where(
                QuizQuestion.subject == subject,
                QuizQuestion.topic == topic,
            )
        )
    ).scalars().all()

    if not fallback:
        logger.warning(f"No questions in bank: subject={subject} topic={topic}")
        return None

    return random.choice(fallback)