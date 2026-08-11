"""
EduMind Learning Resources API

GET  /api/v1/resources/search
GET  /api/v1/resources/{resource_id}
POST /api/v1/resources/seed
"""

import random

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.response import StandardResponse
from models.student import Student
from models.resource import LearningResource
from models.quiz import QuizQuestion
from rag import rag_module
from rag.concept_tree import build_concept_tree_for_topic, extract_key_points
from services.concept_mastery import (
    get_leaf_progress,
    mark_lecture_done,
    record_quiz_result,
    stable_leaf_id,
)
from services.grading import grade as grade_quiz
from services.model_config import model_config_service
from llm import llm_service
from student_profile import student_profile_service
from core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/concept-tree", response_model=StandardResponse)
async def get_concept_tree(
    topic: str = Query(..., min_length=1, description="Curriculum topic key"),
    label: str | None = Query(None, description="Optional Chinese chapter title"),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    Chapter-scoped skill-tree / mastery heatmap.

    Root = chapter; branches = textbook resource titles; leaves = key points
    from stored 教辅. Leaf levels 0–3 come from correct quiz hits.
    """
    profile = await student_profile_service.get_profile(db, current_student.id)
    progress = get_leaf_progress(profile)
    tree = await build_concept_tree_for_topic(
        db, topic=topic, topic_label=label, leaf_progress=progress
    )
    return StandardResponse.ok(
        data=tree,
        message="Concept skill tree built from textbook resources",
    )


class ResourceSeedItem(BaseModel):
    title: str
    subject: str
    topic: str
    content: str
    source: str | None = None


@router.post("/seed", response_model=StandardResponse)
async def seed_resources(
    items: list[ResourceSeedItem],
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Ingest a list of learning resources into the RAG pipeline (idempotent)."""
    seeded = 0
    skipped = 0
    for item in items:
        # Check if already exists by title
        existing = await db.scalar(
            select(LearningResource.id).where(LearningResource.title == item.title)
        )
        if existing:
            skipped += 1
            continue
        await rag_module.upsert_resource(
            db=db,
            title=item.title,
            subject=item.subject,
            topic=item.topic,
            content=item.content,
            source=item.source,
        )
        seeded += 1
    await db.commit()
    return StandardResponse.ok(
        data={"seeded": seeded, "skipped": skipped},
        message=f"Seeded {seeded} resources, skipped {skipped} duplicates",
    )


@router.get("/search", response_model=StandardResponse)
async def search_resources(
    q: str = Query(..., min_length=1),
    limit: int = Query(3, ge=1, le=10),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Query textbooks and reference materials using RAG semantic lookup."""
    resources = await rag_module.retrieve(db, query=q, limit=limit)
    return StandardResponse.ok(
        data=[
            {
                "id": res.id,
                "title": res.title,
                "subject": res.subject,
                "topic": res.topic,
                "source": res.source,
                "content": res.content,
            }
            for res in resources
        ],
        message="Search results retrieved successfully",
    )


# ─────────────────────────────────────────────────────────────────────────
# 叶子级：知识点精讲 / 例题练习
# ─────────────────────────────────────────────────────────────────────────

def _parse_leaf_id(leaf_id: str) -> int | None:
    """leaf-{res_id}-{hash} → res_id"""
    try:
        parts = leaf_id.split("-")
        if len(parts) >= 3 and parts[0] == "leaf":
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


@router.get("/leaf-lecture", response_model=StandardResponse)
async def get_leaf_lecture(
    leaf_id: str = Query(..., min_length=1),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    返回该叶子对应的教辅原文片段（精讲内容，稳定不幻觉）。
    """
    res_id = _parse_leaf_id(leaf_id)
    if res_id is None:
        raise ValidationError("leaf_id 格式非法")
    resource = await db.get(LearningResource, res_id)
    if not resource:
        raise NotFoundError("LearningResource", str(res_id))

    return StandardResponse.ok(
        data={
            "leaf_id": leaf_id,
            "title": resource.title,
            "source": resource.source,
            "content": resource.content,
            "topic": resource.topic,
        },
        message="Leaf lecture retrieved",
    )


class LeafLectureDoneRequest(BaseModel):
    leaf_id: str


@router.post("/leaf-lecture/done", response_model=StandardResponse)
async def set_leaf_lecture_done(
    payload: LeafLectureDoneRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """标记该叶子精讲已学（level +1，上限 3）。"""
    result = await mark_lecture_done(db, current_student.id, payload.leaf_id)
    await db.commit()
    return StandardResponse.ok(data=result, message="Lecture marked done")


@router.get("/leaf-quiz", response_model=StandardResponse)
async def get_leaf_quiz(
    leaf_id: str = Query(..., min_length=1),
    slot: int = Query(1, ge=1, le=2),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    为该叶子取一道练习题。
    第一来源：题库（按 topic + knowledge_tags 命中叶子文案）。
    第二来源：AI 结构化生成（落库后返回）。
    无题且无 Key → 返回 404 提示。
    """
    res_id = _parse_leaf_id(leaf_id)
    resource = await db.get(LearningResource, res_id) if res_id else None
    if not resource:
        raise NotFoundError("LearningResource", str(res_id))

    topic = resource.topic
    subject = resource.subject
    leaf_label = leaf_id  # fallback
    # 反推叶子文案：从 content 切句找包含的片段（粗略）
    points = extract_key_points(resource.content or "", limit=12)
    # 叶子 id 由 res_id + 文案 md5 生成，这里直接用 points 重新匹配
    for p in points:
        if stable_leaf_id(res_id, p) == leaf_id:
            leaf_label = p
            break

    # 1) 题库优先：按 topic + tags 命中叶子文案
    rows = (
        await db.scalars(
            select(QuizQuestion).where(QuizQuestion.topic == topic)
        )
    ).all()
    leaf_label_n = (leaf_label or "").casefold()
    candidates = []
    for q in rows:
        tags = [str(t).strip().casefold() for t in (q.knowledge_tags or [])]
        if tags and any(len(t) >= 2 and (t in leaf_label_n or leaf_label_n in t) for t in tags):
            candidates.append(q)
    if not candidates:
        candidates = list(rows)

    # 排除该 slot 已用过的题
    profile = await student_profile_service.get_profile(db, current_student.id)
    progress = (profile.learning_preferences or {}).get("concept_leaf_progress", {})
    prog = progress.get(leaf_id) or {}
    used_qids = set()
    for s in (1, 2):
        qid = prog.get(f"quiz{s}", {}).get("qid")
        if qid and s != slot:
            used_qids.add(qid)
    pool = [q for q in candidates if q.id not in used_qids] if candidates else []

    if pool:
        q = random.choice(pool)
        return StandardResponse.ok(
            data=_quiz_to_dict(q, leaf_id, slot),
            message="Quiz from bank",
        )

    # 2) AI 兜底生成
    grade = current_student.grade or "高中"
    runtime_key = model_config_service.runtime.llm_api_key
    generated = await llm_service.generate_structured_quiz(
        topic=topic, subject=subject, grade=grade,
        leaf_label=leaf_label, runtime_api_key=runtime_key,
    )
    if not generated:
        return StandardResponse.error(
            code=404,
            message="题库暂无该要点题目，且 AI 未配置或生成失败，请先配置 API Key 或联系管理员入库",
        )

    # 落库
    q = QuizQuestion(
        subject=subject,
        topic=topic,
        grade=grade,
        difficulty=int(generated.get("difficulty", 2) or 2),
        question_type=generated["question_type"],
        stem=generated["stem"],
        options=generated.get("options"),
        correct_answer=generated["correct_answer"],
        knowledge_tags=generated.get("knowledge_tags") or [],
        explanation=None,
    )
    db.add(q)
    await db.flush()
    await db.commit()
    return StandardResponse.ok(
        data=_quiz_to_dict(q, leaf_id, slot),
        message="Quiz generated by AI and saved",
    )


class LeafQuizSubmitRequest(BaseModel):
    leaf_id: str
    slot: int  # 1 or 2
    question_id: int
    user_answer: dict


@router.post("/leaf-quiz/submit", response_model=StandardResponse)
async def submit_leaf_quiz(
    payload: LeafQuizSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """提交叶子练习：规则判分 → 记录到该 slot → 重算 level。"""
    if payload.slot not in (1, 2):
        raise ValidationError("slot must be 1 or 2")
    q = await db.get(QuizQuestion, payload.question_id)
    if not q:
        raise NotFoundError("QuizQuestion", str(payload.question_id))

    grade_result = grade_quiz(q.question_type, q.correct_answer, payload.user_answer)
    is_correct = bool(grade_result["is_correct"])

    result = await record_quiz_result(
        db, current_student.id, payload.leaf_id, payload.slot,
        payload.question_id, is_correct,
    )
    await db.commit()

    return StandardResponse.ok(
        data={
            "score": grade_result["score"],
            "is_correct": is_correct,
            "details": grade_result["details"],
            "correct_answer": q.correct_answer,
            "level": result["level"],
            "progress": result["progress"],
        },
        message="Quiz graded",
    )


def _quiz_to_dict(q: QuizQuestion, leaf_id: str, slot: int) -> dict:
    return {
        "question_id": q.id,
        "leaf_id": leaf_id,
        "slot": slot,
        "question_type": q.question_type,
        "stem": q.stem,
        "options": q.options,
        "difficulty": q.difficulty,
        "knowledge_tags": q.knowledge_tags,
    }


@router.get("/{resource_id}", response_model=StandardResponse)
async def get_resource_detail(
    resource_id: int,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Retrieve full text content of a learning resource by ID."""
    resource = await db.get(LearningResource, resource_id)
    if not resource:
        raise NotFoundError("LearningResource", str(resource_id))

    return StandardResponse.ok(
        data={
            "id": resource.id,
            "title": resource.title,
            "subject": resource.subject,
            "topic": resource.topic,
            "source": resource.source,
            "content": resource.content,
        },
        message="Resource details retrieved successfully",
    )
