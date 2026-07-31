"""
EduMind Learning Resources API

GET  /api/v1/resources/search
GET  /api/v1/resources/{resource_id}
POST /api/v1/resources/seed
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.response import StandardResponse
from models.student import Student
from models.resource import LearningResource
from rag import rag_module
from core.exceptions import NotFoundError

router = APIRouter(prefix="/resources", tags=["resources"])


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
