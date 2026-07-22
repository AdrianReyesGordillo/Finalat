"""Categories router — GET/POST/PUT/DELETE endpoints.

Provides CRUD operations for user categories. System categories (is_system=True)
are protected and cannot be modified or deleted. Default categories are seeded
for new users.

Requirements: 5.6, 5.7, 5.8
"""

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.categories import Category
from backend.models.database import get_db
from backend.utils.response import (
    error_response,
    forbidden_response,
    not_found_response,
    success_response,
    validation_error_response,
)
from backend.utils.validators import ValidationError, validate_and_sanitize_name

router = APIRouter(prefix="/api/categories", tags=["categories"])

# Default categories seeded for every new user
DEFAULT_CATEGORIES = [
    {"name": "Sueldo", "is_system": True},
    {"name": "Creditos", "is_system": True},
    {"name": "Prestamos", "is_system": False},
    {"name": "Otros", "is_system": False},
]


async def seed_default_categories(user_id: str, db: AsyncSession) -> list[Category]:
    """Create default categories for a new user.

    Seeds: Sueldo (system), Creditos (system), Prestamos, Otros.

    Args:
        user_id: The Firebase UID of the new user.
        db: Active async database session.

    Returns:
        List of created Category instances.
    """
    categories = []
    for cat_def in DEFAULT_CATEGORIES:
        category = Category(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=cat_def["name"],
            is_system=cat_def["is_system"],
        )
        db.add(category)
        categories.append(category)
    await db.flush()
    return categories


def _get_user_id(request: Request) -> str:
    """Extract user_id from request state (set by auth middleware)."""
    return request.state.user_id


# --------------------------------------------------------------------------
# GET /api/categories — List all categories for the authenticated user
# --------------------------------------------------------------------------


@router.get("")
async def list_categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return all categories belonging to the authenticated user."""
    user_id = _get_user_id(request)

    stmt = (
        select(Category)
        .where(Category.user_id == user_id)
        .order_by(Category.created_at)
    )
    result = await db.execute(stmt)
    categories = result.scalars().all()

    data = [
        {
            "id": cat.id,
            "name": cat.name,
            "is_system": cat.is_system,
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
        }
        for cat in categories
    ]

    return JSONResponse(status_code=200, content=success_response(data))


# --------------------------------------------------------------------------
# POST /api/categories — Create a new custom category
# --------------------------------------------------------------------------


@router.post("")
async def create_category(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user category.

    Body JSON: { "name": string (max 50 chars) }
    System categories cannot be created via this endpoint.
    """
    user_id = _get_user_id(request)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                "Invalid request body.",
                fields={"body": "Request body must be valid JSON."},
            ),
        )

    raw_name = body.get("name")
    if raw_name is None:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                "Category name is required.",
                fields={"name": "Field cannot be empty."},
            ),
        )

    # Validate and sanitize name (max 50 chars for categories)
    try:
        validated_name = validate_and_sanitize_name(
            str(raw_name), field_name="name", max_length=50
        )
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(e.message, fields={e.field: e.message}),
        )

    # Create the category (always non-system when user-created)
    category = Category(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=validated_name,
        is_system=False,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)

    data = {
        "id": category.id,
        "name": category.name,
        "is_system": category.is_system,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None,
    }

    return JSONResponse(status_code=201, content=success_response(data))


# --------------------------------------------------------------------------
# PUT /api/categories/{id} — Update a category (non-system only)
# --------------------------------------------------------------------------


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update a category name.

    System categories (is_system=True) cannot be modified — returns HTTP 403.
    Body JSON: { "name": string (max 50 chars) }
    """
    user_id = _get_user_id(request)

    # Fetch the category scoped to the user
    stmt = select(Category).where(
        Category.id == category_id, Category.user_id == user_id
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Category not found."),
        )

    # System category protection
    if category.is_system:
        return JSONResponse(
            status_code=403,
            content=forbidden_response(
                "System categories cannot be modified."
            ),
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                "Invalid request body.",
                fields={"body": "Request body must be valid JSON."},
            ),
        )

    raw_name = body.get("name")
    if raw_name is None:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                "Category name is required.",
                fields={"name": "Field cannot be empty."},
            ),
        )

    # Validate and sanitize name
    try:
        validated_name = validate_and_sanitize_name(
            str(raw_name), field_name="name", max_length=50
        )
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(e.message, fields={e.field: e.message}),
        )

    category.name = validated_name
    await db.flush()
    await db.refresh(category)

    data = {
        "id": category.id,
        "name": category.name,
        "is_system": category.is_system,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None,
    }

    return JSONResponse(status_code=200, content=success_response(data))


# --------------------------------------------------------------------------
# DELETE /api/categories/{id} — Delete a category (non-system only)
# --------------------------------------------------------------------------


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a category.

    System categories (is_system=True) cannot be deleted — returns HTTP 403.
    """
    user_id = _get_user_id(request)

    # Fetch the category scoped to the user
    stmt = select(Category).where(
        Category.id == category_id, Category.user_id == user_id
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Category not found."),
        )

    # System category protection
    if category.is_system:
        return JSONResponse(
            status_code=403,
            content=forbidden_response(
                "System categories cannot be deleted."
            ),
        )

    await db.delete(category)
    await db.flush()

    return JSONResponse(
        status_code=200,
        content=success_response({"deleted": True, "id": category_id}),
    )
