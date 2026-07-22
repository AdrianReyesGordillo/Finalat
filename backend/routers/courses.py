"""Courses and Lessons router — endpoints for /api/courses.

Implements:
- GET /api/courses — List all courses with lesson count and sort_order (public)
- GET /api/courses/{id}/lessons — List lessons for a course (public)
- GET /api/courses/{id}/lessons/{lesson_id} — Single lesson content (auth required)
- POST /api/courses/{id}/lessons/{lesson_id}/complete — Mark lesson as complete (auth required)
- GET /api/courses/progress — Get user's overall course progress (auth required)

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.courses import Course, Lesson
from backend.models.database import get_db
from backend.models.lesson_progress import LessonProgress
from backend.utils.response import (
    not_found_response,
    success_response,
    unauthorized_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["courses"])


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware).

    Returns the user_id or None if not authenticated.
    """
    return getattr(request.state, "user_id", None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_courses(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all courses with lesson count and sort_order.

    This is a public endpoint — no authentication required.
    Returns courses sorted by sort_order.
    """
    stmt = select(Course).order_by(Course.sort_order.asc())
    result = await db.execute(stmt)
    courses = result.scalars().all()

    items = []
    for course in courses:
        items.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "lesson_count": course.lesson_count,
            "sort_order": course.sort_order,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        })

    return JSONResponse(status_code=200, content=success_response(items))


@router.get("/progress")
async def get_course_progress(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get user's overall course progress.

    Returns per-course completion stats for the authenticated user.
    Requires authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content=unauthorized_response("Authentication required."),
        )

    # Get all courses
    stmt = select(Course).order_by(Course.sort_order.asc())
    result = await db.execute(stmt)
    courses = result.scalars().all()

    progress_data = []
    for course in courses:
        # Get total lessons for this course
        lessons_stmt = select(func.count(Lesson.id)).where(
            Lesson.course_id == course.id
        )
        lessons_result = await db.execute(lessons_stmt)
        total_lessons = lessons_result.scalar() or 0

        # Get completed lessons for this user in this course
        completed_stmt = (
            select(func.count(LessonProgress.id))
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .where(
                LessonProgress.user_id == user_id,
                Lesson.course_id == course.id,
                LessonProgress.completed == True,
            )
        )
        completed_result = await db.execute(completed_stmt)
        completed_lessons = completed_result.scalar() or 0

        # Calculate progress percentage
        progress_percentage = (
            round((completed_lessons / total_lessons) * 100, 2)
            if total_lessons > 0
            else 0.0
        )

        progress_data.append({
            "course_id": course.id,
            "course_title": course.title,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": progress_percentage,
        })

    return JSONResponse(status_code=200, content=success_response(progress_data))


@router.get("/{course_id}/lessons")
async def list_course_lessons(
    course_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List lessons for a course.

    This is a public endpoint — no authentication required.
    Returns lessons sorted by sort_order.
    """
    # Verify the course exists
    course_stmt = select(Course).where(Course.id == course_id)
    course_result = await db.execute(course_stmt)
    course = course_result.scalar_one_or_none()

    if not course:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Course not found."),
        )

    # Get lessons for this course
    stmt = (
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.sort_order.asc())
    )
    result = await db.execute(stmt)
    lessons = result.scalars().all()

    items = []
    for lesson in lessons:
        items.append({
            "id": lesson.id,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "sort_order": lesson.sort_order,
            "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
            "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
        })

    return JSONResponse(status_code=200, content=success_response({
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
        },
        "lessons": items,
    }))


@router.get("/{course_id}/lessons/{lesson_id}")
async def get_lesson(
    course_id: str,
    lesson_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get single lesson content.

    Requires authentication to access lesson content.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content=unauthorized_response("Authentication required to access lesson content."),
        )

    # Verify the course exists
    course_stmt = select(Course).where(Course.id == course_id)
    course_result = await db.execute(course_stmt)
    course = course_result.scalar_one_or_none()

    if not course:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Course not found."),
        )

    # Get the lesson
    lesson_stmt = select(Lesson).where(
        Lesson.id == lesson_id,
        Lesson.course_id == course_id,
    )
    lesson_result = await db.execute(lesson_stmt)
    lesson = lesson_result.scalar_one_or_none()

    if not lesson:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Lesson not found."),
        )

    # Check if the user has completed this lesson
    progress_stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    progress_result = await db.execute(progress_stmt)
    progress = progress_result.scalar_one_or_none()

    # Check if prior lessons are not completed (provide recommendation)
    prior_lessons_stmt = (
        select(Lesson)
        .where(
            Lesson.course_id == course_id,
            Lesson.sort_order < lesson.sort_order,
        )
        .order_by(Lesson.sort_order.asc())
    )
    prior_result = await db.execute(prior_lessons_stmt)
    prior_lessons = prior_result.scalars().all()

    has_incomplete_prior = False
    if prior_lessons:
        prior_lesson_ids = [l.id for l in prior_lessons]
        completed_prior_stmt = (
            select(func.count(LessonProgress.id))
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(prior_lesson_ids),
                LessonProgress.completed == True,
            )
        )
        completed_prior_result = await db.execute(completed_prior_stmt)
        completed_prior_count = completed_prior_result.scalar() or 0
        has_incomplete_prior = completed_prior_count < len(prior_lesson_ids)

    lesson_data = {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "title": lesson.title,
        "content": lesson.content,
        "sort_order": lesson.sort_order,
        "completed": progress.completed if progress else False,
        "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
        "recommendation": (
            "Se recomienda completar las lecciones anteriores primero."
            if has_incomplete_prior
            else None
        ),
        "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
        "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
    }

    return JSONResponse(status_code=200, content=success_response(lesson_data))


@router.post("/{course_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    course_id: str,
    lesson_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Mark a lesson as complete for the authenticated user.

    Creates or updates a LessonProgress record for the user.
    Requires authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content=unauthorized_response("Authentication required."),
        )

    # Verify the course exists
    course_stmt = select(Course).where(Course.id == course_id)
    course_result = await db.execute(course_stmt)
    course = course_result.scalar_one_or_none()

    if not course:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Course not found."),
        )

    # Verify the lesson exists and belongs to this course
    lesson_stmt = select(Lesson).where(
        Lesson.id == lesson_id,
        Lesson.course_id == course_id,
    )
    lesson_result = await db.execute(lesson_stmt)
    lesson = lesson_result.scalar_one_or_none()

    if not lesson:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Lesson not found."),
        )

    # Check if progress record already exists
    progress_stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    progress_result = await db.execute(progress_stmt)
    progress = progress_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if progress:
        # Update existing progress
        progress.completed = True
        progress.completed_at = now
    else:
        # Create new progress record
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=now,
        )
        db.add(progress)

    await db.flush()
    await db.refresh(progress)

    response_data = {
        "id": progress.id,
        "user_id": progress.user_id,
        "lesson_id": progress.lesson_id,
        "completed": progress.completed,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }

    return JSONResponse(status_code=200, content=success_response(response_data))
