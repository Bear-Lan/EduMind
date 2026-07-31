"""
EduMind Analytics API

GET /api/v1/analytics/dashboard
"""

import datetime
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_student
from schemas.response import StandardResponse
from models.student import Student, StudentProfile
from models.history import LearningHistory

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=StandardResponse)
async def get_analytics_dashboard(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Retrieve multi-dimensional analytics for the student."""
    
    # 1. Fetch Profile for Mastery Map
    profile = await db.scalar(
        select(StudentProfile).where(StudentProfile.student_id == current_student.id)
    )
    mastery_map = profile.mastery_map or {}
    
    # 2. Fetch last 7 days of Learning History
    now = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago = now - datetime.timedelta(days=7)
    
    history_records = await db.scalars(
        select(LearningHistory)
        .where(
            LearningHistory.student_id == current_student.id,
            LearningHistory.timestamp >= seven_days_ago
        )
        .order_by(LearningHistory.timestamp.asc())
    )
    
    # Process history for trends and distributions
    trend_data = defaultdict(int)
    activity_distribution = defaultdict(int)
    
    # Initialize the last 7 days with 0 to ensure continuous dates
    for i in range(7):
        date_str = (now - datetime.timedelta(days=6-i)).strftime("%Y-%m-%d")
        trend_data[date_str] = 0
        
    for record in history_records:
        date_str = record.timestamp.strftime("%Y-%m-%d")
        if date_str in trend_data:
            trend_data[date_str] += record.duration
            
        activity_distribution[record.activity_type] += record.duration
        
    # Format data for charts
    trend_dates = list(trend_data.keys())
    trend_durations = [round(duration / 60) for duration in trend_data.values()] # Convert to minutes
    
    # Standardize activity names for the frontend doughnut chart
    activity_labels = []
    activity_times = []
    activity_name_map = {
        "learning_completion": "章节学习",
        "assessment": "随堂测验",
    }
    for k, v in activity_distribution.items():
        activity_labels.append(activity_name_map.get(k, k))
        activity_times.append(round(v / 60)) # Convert to minutes
        
    # If empty, provide some default mock data just for visual testing
    if not activity_labels:
        activity_labels = ["章节学习", "随堂测验"]
        activity_times = [0, 0]

    return StandardResponse.ok(
        data={
            "mastery_map": mastery_map,
            "trend": {
                "dates": trend_dates,
                "durations_minutes": trend_durations
            },
            "distribution": {
                "labels": activity_labels,
                "durations_minutes": activity_times
            }
        },
        message="Analytics dashboard data retrieved successfully"
    )
