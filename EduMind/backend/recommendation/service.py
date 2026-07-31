"""
EduMind Recommendation Engine Service

Calculates learning path priorities based on student profile mastery maps
and curriculum prerequisite dependencies. Generates structured LearningPlan records.
"""

import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.student import StudentProfile
from models.plan import LearningPlan
from core.exceptions import ValidationError

logger = logging.getLogger(__name__)

MASTERY_THRESHOLD = 0.8  # Core requirement for topic mastery


class RecommendationEngine:
    """Calculates topic priorities and generates structured study plans (Rules-Based)."""

    def calculate_priority(self, student_profile: StudentProfile, curriculum: dict) -> list[dict]:
        """
        Evaluate all unmastered curriculum topics and compute their eligibility and priority.
        """
        mastery_map = student_profile.mastery_map or {}
        priorities = []

        # Remove __zh_names__ to avoid treating it as a topic
        topics_map = {k: v for k, v in curriculum.items() if k != "__zh_names__"}

        for idx, (topic, prereqs) in enumerate(topics_map.items()):
            current_mastery = float(mastery_map.get(topic, 0.0))

            # Skip already mastered topics
            if current_mastery >= MASTERY_THRESHOLD:
                continue

            # Evaluate prerequisites
            eligible = True
            missing_prereqs = []
            for prereq in prereqs:
                prereq_mastery = float(mastery_map.get(prereq, 0.0))
                if prereq_mastery < MASTERY_THRESHOLD:
                    eligible = False
                    missing_prereqs.append(prereq)

            # Score calculations: earlier topics in curriculum get higher priority
            # Max base score is 100, drops by 10 for each subsequent topic index
            priority_score = 0
            if eligible:
                priority_score = max(10, 100 - (idx * 10))

            priorities.append(
                {
                    "topic": topic,
                    "current_mastery": current_mastery,
                    "eligible": eligible,
                    "missing_prerequisites": missing_prereqs,
                    "priority_score": priority_score,
                }
            )

        # Sort eligible topics by priority score descending
        priorities.sort(key=lambda x: (-x["priority_score"], x["topic"]))
        return priorities

    def explain_recommendation(
        self, student_profile: StudentProfile, curriculum: dict, recommended_topic: str
    ) -> dict:
        """
        Produce a structured technical explanation metadata for a recommended topic.

        Note: Outputs structured parameters only. No natural language chat formatting.
        """
        prereqs = curriculum.get(recommended_topic, [])
        mastery_map = student_profile.mastery_map or {}

        # Log mastery levels of prerequisites
        mastery_levels = {p: float(mastery_map.get(p, 0.0)) for p in prereqs}

        reason_code = "PREREQUISITES_MET"
        reason_text = (
            f"All prerequisites ({', '.join(prereqs) or 'None'}) are mastered. "
            f"Ready to begin learning this curriculum milestone."
        )

        return {
            "topic": recommended_topic,
            "code": reason_code,
            "reason": reason_text,
            "metadata": {
                "prerequisites": prereqs,
                "mastery_levels": mastery_levels,
            },
        }

    async def generate_learning_plan(
        self, db: AsyncSession, student_profile: StudentProfile, curriculum: dict, force_topic: str = None
    ) -> LearningPlan | None:
        """
        Generate and persist the next study plan for a student based on eligibility.
        If force_topic is provided, skips priority calculation and recommends the forced topic.
        Saves plan to database and updates profile's last_recommendation metadata.
        """
        if force_topic:
            # Bypass priority filter, but verify topic exists in curriculum
            topics_map = {k: v for k, v in curriculum.items() if k != "__zh_names__"}
            if force_topic not in topics_map:
                logger.warning(f"Forced topic '{force_topic}' not in curriculum.")
            target_topic = force_topic
            logger.info(f"Forcing generation for topic: {target_topic}")
            explanation = self.explain_recommendation(student_profile, curriculum, target_topic)
        else:
            priorities = self.calculate_priority(student_profile, curriculum)
            eligible_topics = [p for p in priorities if p["eligible"]]

            if not eligible_topics:
                # All topics mastered or completed: generate a Review & Reinforcement plan for lowest mastery topic
                logger.info(
                    f"Curriculum completed for student ID {student_profile.student_id}. Generating review plan."
                )
                priorities_sorted = sorted(priorities, key=lambda x: x["current_mastery"])
                topics_keys = [k for k in curriculum.keys() if k != "__zh_names__"]
                target_topic = priorities_sorted[0]["topic"] if priorities_sorted else (topics_keys[0] if topics_keys else "review")
                zh_name = curriculum.get("__zh_names__", {}).get(target_topic, target_topic)
                explanation = {
                    "topic": target_topic,
                    "code": "REVIEW_REINFORCEMENT",
                    "reason": f"已完成基本教学大纲！系统自动为您开启《{zh_name}》的巩固复习与能力拔高计划。",
                    "metadata": {"mastery_levels": {}}
                }
            else:
                # Select highest priority topic
                target_topic = eligible_topics[0]["topic"]
                explanation = self.explain_recommendation(student_profile, curriculum, target_topic)

        # Topic Chinese name mapping from AI generated curriculum
        TOPIC_ZH = curriculum.get("__zh_names__", {})
        topic_zh = TOPIC_ZH.get(target_topic, target_topic)

        # Generate standard step checklist (in Chinese)
        steps = [
            {
                "step_number": 1,
                "title": f"自学核心概念：{topic_zh}",
                "description": f"阅读本章节的基础定义与核心公式，建立对《{topic_zh}》的初步认知框架，完成 AI 教练的知识点精讲。",
                "completed": False,
            },
            {
                "step_number": 2,
                "title": f"完成练习题：{topic_zh}",
                "description": f"在右侧'AI 教练答疑'区向教练提问或请求出题，完成至少 3 道关于《{topic_zh}》的练习题，并与教练深入探讨解题思路。",
                "completed": False,
            },
            {
                "step_number": 3,
                "title": f"通过掌握度测验：{topic_zh}",
                "description": f"点击'标记完成'上报本章节学习结果。系统将记录你的掌握情况（≥80分即视为掌握），并自动解锁下一阶段推荐任务。",
                "completed": False,
            },
        ]

        # Save to database
        plan = LearningPlan(
            student_id=student_profile.student_id,
            target_topic=target_topic,
            learning_steps=steps,
            recommendation_reason=explanation["reason"],
            status="active",
        )
        db.add(plan)
        await db.flush()

        # Update profile's last recommendation timestamp
        student_profile.last_recommendation = {
            "topic": target_topic,
            "reason_code": explanation["code"],
            "reason": explanation["reason"],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        await db.flush()

        logger.info(
            f"Generated new active LearningPlan ID {plan.id} for student ID {student_profile.student_id}"
        )
        return plan
