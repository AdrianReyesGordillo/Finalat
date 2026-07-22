"""Unit tests for the Courses and Lessons router.

Tests cover:
- GET /api/courses — list all courses (public)
- GET /api/courses/{id}/lessons — list lessons for a course (public)
- GET /api/courses/{id}/lessons/{lesson_id} — single lesson content (auth required)
- POST /api/courses/{id}/lessons/{lesson_id}/complete — mark lesson complete (auth required)
- GET /api/courses/progress — user course progress (auth required)

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.models.courses import Course, Lesson
from backend.models.database import Base, get_db
from backend.models.lesson_progress import LessonProgress
from backend.models.user import User
from backend.routers.courses import router as courses_router
from backend.utils.response import success_response


# ---------------------------------------------------------------------------
# Test Database Setup
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_USER_ID = "test-user-uid-123"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override the database dependency with a test session."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Test App Setup (isolated from main app)
# ---------------------------------------------------------------------------


class MockAuthMiddleware(BaseHTTPMiddleware):
    """Test middleware that sets user_id based on the X-Test-User-Id header."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        user_id = request.headers.get("x-test-user-id")
        request.state.user_id = user_id  # None if header not present
        return await call_next(request)


def create_test_app() -> FastAPI:
    """Create a test FastAPI app with the courses router."""
    test_app = FastAPI()
    test_app.add_middleware(MockAuthMiddleware)
    test_app.include_router(courses_router)
    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


test_app = create_test_app()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        user_id=TEST_USER_ID,
        email="test@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def test_course(db_session):
    """Create a test course with lessons."""
    course = Course(
        id=str(uuid.uuid4()),
        title="Python Basics",
        description="Learn Python from scratch",
        lesson_count=3,
        sort_order=1,
    )
    db_session.add(course)
    await db_session.flush()

    lessons = []
    for i in range(3):
        lesson = Lesson(
            id=str(uuid.uuid4()),
            course_id=course.id,
            title=f"Lesson {i + 1}",
            content=f"Content for lesson {i + 1}",
            sort_order=i + 1,
        )
        db_session.add(lesson)
        lessons.append(lesson)

    await db_session.commit()
    return course, lessons


def _auth_headers(user_id: str = TEST_USER_ID) -> dict:
    """Return headers that simulate an authenticated user."""
    return {"X-Test-User-Id": user_id}


# ---------------------------------------------------------------------------
# Tests — List Courses (Public)
# ---------------------------------------------------------------------------


class TestListCourses:
    """Tests for GET /api/courses endpoint."""

    @pytest.mark.asyncio
    async def test_list_courses_returns_empty_list(self, setup_database):
        """Should return empty list when no courses exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/courses")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_list_courses_returns_courses(self, test_course):
        """Should return courses sorted by sort_order."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/courses")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["title"] == "Python Basics"
        assert body["data"][0]["lesson_count"] == 3
        assert body["data"][0]["sort_order"] == 1

    @pytest.mark.asyncio
    async def test_list_courses_no_auth_required(self, test_course):
        """Should work without authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # No auth headers
            response = await client.get("/api/courses")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True


# ---------------------------------------------------------------------------
# Tests — List Course Lessons (Public)
# ---------------------------------------------------------------------------


class TestListCourseLessons:
    """Tests for GET /api/courses/{id}/lessons endpoint."""

    @pytest.mark.asyncio
    async def test_course_not_found(self, setup_database):
        """Should return 404 when course doesn't exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/courses/{uuid.uuid4()}/lessons")

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_lessons_for_course(self, test_course):
        """Should return lessons for an existing course."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/courses/{course.id}/lessons")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["course"]["title"] == "Python Basics"
        assert len(body["data"]["lessons"]) == 3
        assert body["data"]["lessons"][0]["title"] == "Lesson 1"
        assert body["data"]["lessons"][1]["title"] == "Lesson 2"
        assert body["data"]["lessons"][2]["title"] == "Lesson 3"

    @pytest.mark.asyncio
    async def test_lessons_no_auth_required(self, test_course):
        """Should work without authentication."""
        course, _ = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/courses/{course.id}/lessons")

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests — Get Single Lesson (Auth Required)
# ---------------------------------------------------------------------------


class TestGetLesson:
    """Tests for GET /api/courses/{id}/lessons/{lesson_id} endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self, test_course):
        """Should return 401 when not authenticated."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}"
            )

        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_lesson_not_found(self, test_course, test_user):
        """Should return 404 when lesson doesn't exist."""
        course, _ = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/courses/{course.id}/lessons/{uuid.uuid4()}",
                headers=_auth_headers(),
            )

        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_returns_lesson_with_content(self, test_course, test_user):
        """Should return lesson content for authenticated user."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["title"] == "Lesson 1"
        assert body["data"]["content"] == "Content for lesson 1"
        assert body["data"]["completed"] is False
        assert body["data"]["recommendation"] is None  # First lesson, no prior

    @pytest.mark.asyncio
    async def test_shows_recommendation_for_incomplete_prior(self, test_course, test_user):
        """Should recommend completing prior lessons if they aren't done."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Access lesson 3 without completing lessons 1 and 2
            response = await client.get(
                f"/api/courses/{course.id}/lessons/{lessons[2].id}",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["recommendation"] is not None
        assert "lecciones anteriores" in body["data"]["recommendation"]


# ---------------------------------------------------------------------------
# Tests — Complete Lesson (Auth Required)
# ---------------------------------------------------------------------------


class TestCompleteLesson:
    """Tests for POST /api/courses/{id}/lessons/{lesson_id}/complete endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self, test_course):
        """Should return 401 when not authenticated."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete"
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_course_not_found(self, test_user):
        """Should return 404 when course doesn't exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/courses/{uuid.uuid4()}/lessons/{uuid.uuid4()}/complete",
                headers=_auth_headers(),
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_lesson_not_found(self, test_course, test_user):
        """Should return 404 when lesson doesn't exist."""
        course, _ = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/courses/{course.id}/lessons/{uuid.uuid4()}/complete",
                headers=_auth_headers(),
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_marks_lesson_as_complete(self, test_course, test_user):
        """Should create a progress record marking lesson complete."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["completed"] is True
        assert body["data"]["lesson_id"] == lessons[0].id
        assert body["data"]["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_idempotent_completion(self, test_course, test_user):
        """Should handle marking an already-completed lesson as complete."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Complete the lesson twice
            await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete",
                headers=_auth_headers(),
            )
            response = await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["completed"] is True


# ---------------------------------------------------------------------------
# Tests — Course Progress (Auth Required)
# ---------------------------------------------------------------------------


class TestCourseProgress:
    """Tests for GET /api/courses/progress endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self, setup_database):
        """Should return 401 when not authenticated."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get("/api/courses/progress")

        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False

    @pytest.mark.asyncio
    async def test_returns_empty_progress_when_no_courses(self, test_user):
        """Should return empty progress when no courses exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/courses/progress",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_returns_progress_with_completions(self, test_course, test_user):
        """Should return per-course progress percentage."""
        course, lessons = test_course

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Complete 2 out of 3 lessons
            await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete",
                headers=_auth_headers(),
            )
            await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[1].id}/complete",
                headers=_auth_headers(),
            )

            # Get progress
            response = await client.get(
                "/api/courses/progress",
                headers=_auth_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["course_title"] == "Python Basics"
        assert body["data"][0]["total_lessons"] == 3
        assert body["data"][0]["completed_lessons"] == 2
        assert body["data"][0]["progress_percentage"] == 66.67

    @pytest.mark.asyncio
    async def test_progress_scoped_to_user(self, test_course, test_user):
        """Should only show progress for the authenticated user."""
        course, lessons = test_course

        # Complete as test user
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            await client.post(
                f"/api/courses/{course.id}/lessons/{lessons[0].id}/complete",
                headers=_auth_headers(),
            )

        # Create another user
        other_user_id = "other-user-uid-456"
        async with TestSessionLocal() as session:
            other_user = User(
                user_id=other_user_id,
                email="other@example.com",
                display_name="Other User",
            )
            session.add(other_user)
            await session.commit()

        # Check progress as different user — should show 0 completions
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/courses/progress",
                headers=_auth_headers(other_user_id),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"][0]["completed_lessons"] == 0
        assert body["data"][0]["progress_percentage"] == 0.0
