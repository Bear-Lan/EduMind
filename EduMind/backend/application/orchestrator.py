"""
EduMind Learning Orchestrator

The central coordinator of all business modules.
This is the ONLY component allowed to coordinate multiple business modules.

Responsibilities:
- Determine workflow
- Invoke business modules in correct order
- Transfer intermediate results
- Handle errors from modules
"""

import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.student import StudentProfile
from models.plan import LearningPlan
from models.history import LearningHistory
from models.chat import ChatSession, ChatMessage

from student_profile import student_profile_service
from recommendation import recommendation_engine
from rag import rag_module
from llm import llm_service
from core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class LearningOrchestrator:
    """
    Central orchestrator for all EduMind business workflows.

    Coordinates between: StudentProfileService, RecommendationEngine, RAGModule, and LLMService.
    """

    async def handle_chat(
        self, db: AsyncSession, student_id: int, message: str, runtime_api_key: str = "",
        mode: str = "normal",
    ) -> dict:
        """
        Orchestrate: Student Profile → RAG → LLM → History Save → Response

        mode: "normal" or "socratic" — passed through to LLM service.
        """
        logger.info(f"[Orchestrator] handle_chat called for student: {student_id}, mode={mode}")

        # 1. Fetch student profile
        profile = await student_profile_service.get_profile(db, student_id)

        from models.student import Student
        student = await db.scalar(select(Student).where(Student.id == student_id))
        subject = (student.subject if student else None) or "数学"
        grade = (student.grade if student else None) or (profile.current_goal or "通用").split()[0]

        # 2. Retrieve RAG educational context (scoped to subject/grade — no cross-subject)
        scored = await rag_module.retrieve_scored(
            db,
            query=message,
            limit=3,
            subject=subject,
            grade=grade,
        )
        resources = [res for res, _ in scored]
        context_string = rag_module.build_context(resources)

        # 2.5 Hard-constraint refusal: no reliable textbook retrieved → refuse
        #     without calling the LLM (prevents fabrication, saves API cost).
        if not resources:
            insufficient_msg = (
                "资料不足：未能在教材知识库中找到与您的问题相关度足够的内容。"
                "请尝试更换关键词，或联系管理员补充相关教材资料。"
            )
            session = await db.scalar(
                select(ChatSession)
                .where(ChatSession.student_id == student_id)
                .order_by(ChatSession.updated_at.desc())
                .limit(1)
            )
            if not session:
                session = ChatSession(
                    student_id=student_id, conversation_summary="学习答疑"
                )
                db.add(session)
                await db.flush()
            db.add(ChatMessage(
                session_id=session.id, role="user", content=message,
            ))
            db.add(ChatMessage(
                session_id=session.id, role="assistant", content=insufficient_msg,
            ))
            session.updated_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()
            logger.info("[Orchestrator] Refusal: no context retrieved, skipping LLM")
            return {
                "session_id": session.id,
                "response": insufficient_msg,
                "references": [],
            }

        # 3. Format Student Context Summary
        profile_summary = (
            f"目标: {profile.current_goal or '无'} | "
            f"当前掌握度: {profile.mastery_map or {}}"
        )

        # 3.5 For Socratic mode, fetch recent conversation history to give the LLM context
        conversation_history = ""
        if mode == "socratic":
            session = await db.scalar(
                select(ChatSession)
                .where(ChatSession.student_id == student_id)
                .order_by(ChatSession.updated_at.desc())
                .limit(1)
            )
            if session:
                recent = await db.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session.id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(10)
                )
                msgs = list(reversed(recent.all()))
                if msgs:
                    lines = []
                    for m in msgs:
                        role = "学生" if m.role == "user" else "教练"
                        lines.append(f"{role}: {m.content[:200]}")
                    conversation_history = "\n".join(lines)

        # 4. Generate AI Coach response
        ai_response = await llm_service.chat(
            prompt=message, context=context_string, profile_summary=profile_summary,
            grade=grade, runtime_api_key=runtime_api_key,
            mode=mode, conversation_history=conversation_history,
        )

        # 5. Save conversation history
        # Find the student's latest active chat session, or create one
        session = await db.scalar(
            select(ChatSession)
            .where(ChatSession.student_id == student_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(1)
        )
        if not session:
            session = ChatSession(student_id=student_id, conversation_summary="学习答疑")
            db.add(session)
            await db.flush()

        # Save user query
        user_msg = ChatMessage(session_id=session.id, role="user", content=message)
        db.add(user_msg)

        # Save AI reply
        ai_msg = ChatMessage(
            session_id=session.id, role="assistant", content=ai_response
        )
        db.add(ai_msg)

        # Update session timestamp
        session.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await db.flush()

        return {
            "session_id": session.id,
            "response": ai_response,
            "references": rag_module.build_references(scored, query=message),
        }

    async def handle_learning_plan(self, db: AsyncSession, student_id: int, runtime_api_key: str = "", force_topic: str = None) -> dict:
        """
        Orchestrate: Student Profile → Active Check → Recommendation Engine → RAG → LLM Guide → Plan
        """
        logger.info(
            f"[Orchestrator] handle_learning_plan called for student: {student_id}"
        )

        # 1. Fetch student profile and student record
        from sqlalchemy import select
        from models.student import Student
        profile = await student_profile_service.get_profile(db, student_id)
        student = await db.scalar(select(Student).where(Student.id == student_id))

        # Get curriculum for subject
        prefs = dict(profile.learning_preferences or {})
        curricula = prefs.get("curricula", {})
        subject = student.subject or "数学"
        grade = (student.grade if student else "") or ""
        goal = (profile.current_goal if profile else "") or f"{grade} {subject}".strip()
        curriculum_key = goal if goal else subject
        
        curriculum = curricula.get(subject)
        
        if not curriculum or len(curriculum.get("__zh_names__", {})) <= 6:
            logger.info(f"Fallback/refresh curriculum generation for {curriculum_key} in orchestrator")
            curriculum = await llm_service.generate_curriculum(curriculum_key, runtime_api_key)
            curricula[subject] = curriculum
            prefs["curricula"] = curricula
            profile.learning_preferences = prefs
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(profile, "learning_preferences")
            await db.flush()

        # 2. Check if an active plan exists for the CURRENT subject curriculum
        plan = None
        if not force_topic:
            active_plan = await db.scalar(
                select(LearningPlan)
                .where(
                    LearningPlan.student_id == student_id,
                    LearningPlan.status == "active",
                )
                .order_by(LearningPlan.id.desc())
                .limit(1)
            )
            if active_plan:
                # Check if the active plan's topic belongs to the current subject curriculum
                topics_in_curriculum = {k for k in curriculum.keys() if k != "__zh_names__"}
                if active_plan.target_topic in topics_in_curriculum:
                    plan = active_plan
                else:
                    logger.info(
                        f"Active plan {active_plan.id} (topic: '{active_plan.target_topic}') "
                        f"does not belong to current subject '{subject}'. Suspending it."
                    )
                    active_plan.status = "suspended"
                    await db.flush()

        # 3. Generate a new plan if none is active for current subject
        if not plan:
            plan = await recommendation_engine.generate_learning_plan(db, profile, curriculum, force_topic)
            # Commit immediately after plan generation to release DB lock 
            # before potentially waiting for LLM call below.
            await db.commit()

        # 4. If a plan exists or was generated, build an AI guide
        ai_guide = None
        if plan:
            if plan.ai_guide:
                ai_guide = plan.ai_guide
            else:
                # Retrieve segment textbooks for RAG context (scoped to subject/grade)
                resources = await rag_module.retrieve(
                    db,
                    query=plan.target_topic,
                    limit=2,
                    subject=subject,
                    grade=grade or None,
                )
                context_string = rag_module.build_context(resources)

                # Generate concept guide for current subject and grade stage
                ai_guide = await llm_service.explain(
                    concept=plan.target_topic,
                    context=context_string,
                    subject=subject,
                    grade=grade or "通用",
                    runtime_api_key=runtime_api_key
                )
                # Cache it in the database
                plan.ai_guide = ai_guide
                await db.commit()

        return {
            "plan_id": plan.id if plan else None,
            "target_topic": plan.target_topic if plan else None,
            "learning_steps": plan.learning_steps if plan else [],
            "reason": plan.recommendation_reason if plan else "所有课程已完全掌握！",
            "ai_guide": ai_guide
            if plan
            else "恭喜你！整个课程大纲已全部学完，太棒了！",
        }

    async def handle_assessment(
        self, db: AsyncSession, student_id: int, assessment_data: dict
    ) -> dict:
        """
        Orchestrate: History Save → Update Mastery → Recommendation Engine → New Plan
        """
        logger.info(
            f"[Orchestrator] handle_assessment called for student: {student_id}"
        )

        topic = assessment_data.get("topic")
        score = assessment_data.get("score")
        duration = assessment_data.get("duration", 0)

        if not topic or score is None:
            raise ValidationError("assessment_data must contain 'topic' and 'score'")

        # 1. Save assessment record to learning history
        history = LearningHistory(
            student_id=student_id,
            activity_type="assessment",
            topic=topic,
            duration=duration,
            result={"score": float(score)},
        )
        db.add(history)
        await db.flush()

        # 2. Update Student Profile mastery rate
        profile = await student_profile_service.update_mastery(
            db, student_id, {topic: float(score)}
        )

        # 3. Automatically trigger new recommendation sequence
        from models.student import Student
        student = await db.scalar(select(Student).where(Student.id == student_id))
        subject = (student.subject if student else None) or "数学"
        prefs = dict(profile.learning_preferences or {})
        curricula = prefs.get("curricula", {})
        curriculum = curricula.get(subject) or {}

        new_plan = await recommendation_engine.generate_learning_plan(db, profile, curriculum)

        return {
            "updated_mastery": profile.mastery_map,
            "new_plan_id": new_plan.id if new_plan else None,
            "recommended_topic": new_plan.target_topic if new_plan else None,
            "reason": new_plan.recommendation_reason if new_plan else "课程已完全掌握！",
        }

    async def handle_learning_completion(
        self, db: AsyncSession, student_id: int, completion_data: dict
    ) -> dict:
        """
        Orchestrate: Complete Step → Check Plan Completion → Update Progress → Save History → Response
        """
        logger.info(
            f"[Orchestrator] handle_learning_completion called for student: {student_id}"
        )

        plan_id = completion_data.get("plan_id")
        step_number = completion_data.get("step_number")
        score = completion_data.get("score", 1.0)
        duration = completion_data.get("duration", 0)

        if not plan_id or not step_number:
            raise ValidationError("completion_data must contain 'plan_id' and 'step_number'")

        # 1. Fetch the active plan
        plan = await db.get(LearningPlan, plan_id)
        if not plan or plan.student_id != student_id:
            raise NotFoundError("LearningPlan", str(plan_id))

        # 2. Mark step completed
        steps = list(plan.learning_steps or [])
        step_found = False
        for step in steps:
            if step["step_number"] == step_number:
                step["completed"] = True
                step_found = True
                break

        if not step_found:
            raise ValidationError(f"Step number {step_number} not found in plan {plan_id}")

        # Save mutated list
        from sqlalchemy.orm.attributes import flag_modified
        plan.learning_steps = steps
        flag_modified(plan, "learning_steps")

        # 3. Check if all steps are completed
        all_completed = all(step["completed"] for step in steps)
        if all_completed:
            plan.status = "completed"

        # 4. Update Student Profile mastery rate
        completed_steps = sum(1 for step in steps if step.get("completed"))
        total_steps = len(steps)
        progress = completed_steps / total_steps if total_steps > 0 else 1.0
        
        # For the final assessment step, if a specific score was provided, use that instead of 1.0
        if all_completed and step_number == total_steps and score < 1.0:
            progress = float(score)
            
        profile = await student_profile_service.update_learning_progress(
            db, student_id, {"topic": plan.target_topic, "score": progress}
        )

        # 5. Record learning history
        history = LearningHistory(
            student_id=student_id,
            activity_type="learning_completion",
            topic=plan.target_topic,
            duration=duration,
            result={
                "plan_id": plan.id,
                "step_number": step_number,
                "all_steps_completed": all_completed,
            },
        )
        db.add(history)
        await db.flush()

        return {
            "step_completed": step_number,
            "all_steps_completed": all_completed,
            "current_mastery": profile.mastery_map,
            "plan_status": plan.status,
        }


# Singleton instance
orchestrator = LearningOrchestrator()
