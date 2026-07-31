"""
EduMind Knowledge Graph API

GET /api/v1/knowledge-graph — 返回当前 subject 的知识拓扑 + mastery
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.response import StandardResponse
from models.student import Student, StudentProfile

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.get("", response_model=StandardResponse)
async def get_knowledge_graph(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """
    返回当前 subject 的知识拓扑：
    - nodes: [{id, label, mastery}]  mastery ∈ [0,1]
    - edges: [{source, target}]      有向依赖边
    """
    profile = (await db.execute(
        __import__("sqlalchemy").select(StudentProfile).where(
            StudentProfile.student_id == current_student.id
        )
    )).scalar_one_or_none()

    subject = current_student.subject or "数学"
    curriculum = {}
    if profile and profile.learning_preferences:
        curriculum = (
            profile.learning_preferences.get("curricula", {}).get(subject, {})
        )

    zh_names = curriculum.get("__zh_names__", {})
    mastery_map = profile.mastery_map if profile else {}

    nodes = []
    edges = []
    for topic_key, prereqs in curriculum.items():
        if topic_key == "__zh_names__":
            continue
        nodes.append({
            "id": topic_key,
            "label": zh_names.get(topic_key, topic_key),
            "mastery": float(mastery_map.get(topic_key, 0.0)),
        })
        for p in prereqs or []:
            edges.append({"source": p, "target": topic_key})

    return StandardResponse.ok(
        data={
            "subject": subject,
            "nodes": nodes,
            "edges": edges,
        },
        message="知识图谱已加载",
    )