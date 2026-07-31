"""
EduMind Assessment API

改造：走结构化题库 + 规则判分。LLM 仅用于生成题目的"解析（explanation）"和评语。

GET  /api/v1/assessment/result            当前 mastery_map
GET  /api/v1/assessment/quiz?topic=xxx    从题库抽一题（自适应难度）
POST /api/v1/assessment/submit            提交作答 → 规则判分 + LLM 评语
POST /api/v1/assessment                   （旧接口）直接提交分数 → 更新 mastery
GET  /api/v1/assessment/error-book        错题本
GET  /api/v1/assessment/history           历史测评
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.assessment import AssessmentSubmitRequest, QuizSubmitRequest
from schemas.response import StandardResponse
from models.student import Student, StudentProfile
from models.quiz import QuizQuestion, QuizAttempt
from application.orchestrator import orchestrator
from student_profile import student_profile_service
from llm import llm_service
from services.grading import grade
from services.quiz_selector import pick_question

router = APIRouter(prefix="/assessment", tags=["assessment"])


# ─────────────────────────────────────────────────────────────────────────
# 旧接口（兼容）：POST /assessment  — 直接给分数（用于"完成学习打卡"场景）
# ─────────────────────────────────────────────────────────────────────────

@router.post("", response_model=StandardResponse)
async def submit_assessment(
    payload: AssessmentSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """旧兼容接口：直接给一个分（0~1）。"""
    res = await orchestrator.handle_assessment(
        db=db,
        student_id=current_student.id,
        assessment_data={
            "topic": payload.topic,
            "score": payload.score,
            "duration": payload.duration,
        },
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="Assessment submitted and profile updated successfully",
    )


@router.get("/result", response_model=StandardResponse)
async def get_latest_result(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """获取当前 mastery_map。"""
    profile = await student_profile_service.get_profile(db, current_student.id)
    return StandardResponse.ok(
        data={"mastery_map": profile.mastery_map or {}},
        message="Assessment results retrieved successfully",
    )


# ─────────────────────────────────────────────────────────────────────────
# 新接口：从题库抽一题
# ─────────────────────────────────────────────────────────────────────────

@router.get("/quiz", response_model=StandardResponse)
async def fetch_quiz(
    topic: str = Query(..., min_length=1),
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    从题库抽一题。难度由学生 mastery 自适应。

    返回：
    - question_id
    - question_type / stem / options
    - difficulty
    """
    profile = await student_profile_service.get_profile(db, current_student.id)
    mastery = (profile.mastery_map or {}).get(topic, 0.0)
    subject = current_student.subject or "数学"

    # 主查找：当前 subject + topic
    q = await pick_question(
        db,
        subject=subject,
        topic=topic,
        student_id=current_student.id,
        mastery=mastery,
    )

    # 兜底：忽略 subject，只按 topic 找（兼容旧 demo 数据里 subject 不规范的情况）
    if not q:
        from sqlalchemy import select
        rows = (await db.execute(
            select(QuizQuestion).where(QuizQuestion.topic == topic)
        )).scalars().all()
        # 排除最近做过的题
        recent_qids = set((await db.execute(
            select(QuizAttempt.question_id)
            .where(QuizAttempt.student_id == current_student.id)
            .order_by(QuizAttempt.created_at.desc())
            .limit(5)
        )).scalars().all())
        rows = [r for r in rows if r.id not in recent_qids]
        if rows:
            import random
            q = random.choice(rows)

    if not q:
        return StandardResponse.error(
            code=404, message=f"题库暂无「{subject} / {topic}」题目，请先联系管理员入库"
        )

    # 标准化返回（不返回正确答案，避免前端泄漏）
    return StandardResponse.ok(
        data={
            "question_id": q.id,
            "question_type": q.question_type,
            "stem": q.stem,
            "options": q.options,
            "difficulty": q.difficulty,
            "knowledge_tags": q.knowledge_tags,
            "subject": q.subject,
            "topic": q.topic,
        },
        message="题目已抽取",
    )


# ─────────────────────────────────────────────────────────────────────────
# 新接口：提交作答 → 规则判分 + LLM 评语 + 更新 mastery
# ─────────────────────────────────────────────────────────────────────────

@router.post("/submit", response_model=StandardResponse)
async def submit_quiz(
    payload: QuizSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    学生提交单题作答。
    1) 规则判分（客观）
    2) 写 quiz_attempts
    3) LLM 生成评语（可选，无 key 时用模板）
    4) 更新 mastery（走 orchestrator，保持现有行为）
    """
    q = await db.get(QuizQuestion, payload.question_id)
    if not q:
        return StandardResponse.error(code=404, message="题目不存在")

    # 1) 规则判分
    grade_result = grade(q.question_type, q.correct_answer, payload.user_answer)
    score = grade_result["score"]
    is_correct = grade_result["is_correct"]
    details = grade_result["details"]

    # 2) LLM 评语（异步生成；key 缺失时降级）
    api_key = payload.runtime_api_key or ""
    try:
        llm_out = await llm_service.grade_answer(
            topic=q.topic,
            question=q.stem,
            answer=str(payload.user_answer.get("answer") or payload.user_answer.get("text") or ""),
            runtime_api_key=api_key,
        )
        feedback = llm_out.get("feedback") if isinstance(llm_out, dict) else str(llm_out)
        if not feedback:
            feedback = details
    except Exception as exc:
        logger.warning(f"LLM feedback failed, fallback: {exc}")
        feedback = details

    # 合并：评语末尾追加规则判分说明
    feedback_full = f"{feedback}\n\n---\n📊 **客观判分**：{details}（得分 {round(score*100)} 分）"

    # 3) 写 attempts
    attempt = QuizAttempt(
        student_id=current_student.id,
        question_id=q.id,
        subject=q.subject,
        topic=q.topic,
        difficulty=q.difficulty,
        user_answer=payload.user_answer,
        is_correct=1 if is_correct else 0,
        score=score,
        feedback=feedback_full,
        duration_seconds=payload.duration or 0,
    )
    db.add(attempt)
    await db.flush()

    # 4) 更新 mastery（沿用现有 orchestrator 逻辑）
    orchestrator_result = await orchestrator.handle_assessment(
        db=db,
        student_id=current_student.id,
        assessment_data={
            "topic": q.topic,
            "score": score,
            "duration": payload.duration or 0,
        },
    )
    await db.commit()

    return StandardResponse.ok(
        data={
            "score": score,
            "is_correct": is_correct,
            "feedback": feedback_full,
            "details": details,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "attempt_id": attempt.id,
            "new_mastery": orchestrator_result.get("updated_mastery"),
        },
        message="判分完成",
    )


# ─────────────────────────────────────────────────────────────────────────
# 错题本
# ─────────────────────────────────────────────────────────────────────────

@router.get("/error-book", response_model=StandardResponse)
async def get_error_book(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """返回错题（is_correct=0 的最新 attempt 列表，含原题信息）。"""
    # 用 JOIN 一次性取出，避免 lazy load 触发 MissingGreenlet
    stmt = (
        select(QuizAttempt, QuizQuestion)
        .join(QuizQuestion, QuizAttempt.question_id == QuizQuestion.id)
        .where(
            QuizAttempt.student_id == current_student.id,
            QuizAttempt.is_correct == 0,
        )
        .order_by(QuizAttempt.created_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).all()

    items = []
    for a, q in rows:
        items.append({
            "attempt_id": a.id,
            "question_id": a.question_id,
            "subject": a.subject,
            "topic": a.topic,
            "difficulty": a.difficulty,
            "stem": q.stem,
            "options": q.options,
            "question_type": q.question_type,
            "user_answer": a.user_answer,
            "correct_answer": q.correct_answer,
            "feedback": a.feedback,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return StandardResponse.ok(
        data={"items": items, "count": len(items)},
        message="错题本已加载",
    )


# ─────────────────────────────────────────────────────────────────────────
# 测评历史
# ─────────────────────────────────────────────────────────────────────────

@router.get("/history", response_model=StandardResponse)
async def get_history(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
) -> StandardResponse:
    """最近 N 条作答记录。"""
    stmt = (
        select(QuizAttempt, QuizQuestion)
        .join(QuizQuestion, QuizAttempt.question_id == QuizQuestion.id)
        .where(QuizAttempt.student_id == current_student.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    items = []
    for a, q in rows:
        items.append({
            "attempt_id": a.id,
            "question_id": a.question_id,
            "subject": a.subject,
            "topic": a.topic,
            "difficulty": a.difficulty,
            "question_type": q.question_type,
            "is_correct": bool(a.is_correct),
            "score": a.score,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return StandardResponse.ok(
        data={"items": items, "count": len(items)},
        message="测评历史已加载",
    )


# ─────────────────────────────────────────────────────────────────────────
# 兼容旧接口（保留原 generate / grade 接口，避免前端断链）
# ─────────────────────────────────────────────────────────────────────────

@router.get("/generate", response_model=StandardResponse)
async def generate_quiz_for_topic_legacy(
    topic: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """兼容旧接口：等同于 /quiz。"""
    return await fetch_quiz(topic=topic, current_student=current_student, db=db)


@router.post("/grade", response_model=StandardResponse)
async def grade_quiz_answer_legacy(
    payload: AssessmentSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """兼容旧接口：根据 payload.topic 找一道题给 LLM 评分（仅 fallback 路径）。"""
    qtext = await llm_service.generate_quiz(topic=payload.topic, runtime_api_key="")
    res = await llm_service.grade_answer(
        topic=payload.topic, question=qtext, answer="", runtime_api_key=""
    )
    return StandardResponse.ok(data=res, message="graded")