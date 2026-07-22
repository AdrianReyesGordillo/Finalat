"""User model — maps to the users table."""

from datetime import datetime, timezone

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class User(Base):
    """Firebase-authenticated user."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(128), primary_key=True, comment="Firebase UID"
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships (cascade delete)
    ahorro = relationship("Ahorro", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    creditos = relationship("Credito", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    gastos_ingresos = relationship("GastoIngreso", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    deudas = relationship("Deuda", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    aportaciones = relationship("Aportacion", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    afore = relationship("Afore", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    gbm_portfolio = relationship("GbmPortfolio", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    lesson_progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    conversation_sessions = relationship("ConversationSession", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    update_tracker = relationship("UpdateTracker", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
