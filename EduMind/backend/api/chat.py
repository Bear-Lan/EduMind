"""
EduMind AI Chat API

POST /api/v1/chat
GET /api/v1/chat/history
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.chat import ChatRequest, ChatResponse, ChatHistoryItem
from schemas.response import StandardResponse
from models.student import Student
from models.chat import ChatSession, ChatMessage
from application.orchestrator import orchestrator

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=StandardResponse[ChatResponse])
async def chat_with_coach(
    payload: ChatRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ChatResponse]:
    """Submit a question to the AI Coach and receive a structured RAG-LLM response."""
    res = await orchestrator.handle_chat(
        db, current_student.id, payload.message
    )
    await db.commit()
    return StandardResponse.ok(
        data=res,
        message="AI response generated successfully",
    )


@router.get("/history", response_model=StandardResponse[list[ChatHistoryItem]])
async def get_chat_history(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[list[ChatHistoryItem]]:
    """Retrieve log messages of the student's latest active dialogue session."""
    session = await db.scalar(
        select(ChatSession)
        .where(ChatSession.student_id == current_student.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(1)
    )
    if not session:
        return StandardResponse.ok(
            data=[],
            message="No chat session found",
        )

    messages = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )

    return StandardResponse.ok(
        data=list(messages.all()),
        message="Chat history retrieved successfully",
    )
