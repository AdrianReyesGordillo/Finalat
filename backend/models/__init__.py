"""SQLAlchemy models package — imports all models for metadata registration."""

from backend.models.database import Base, engine, async_session, get_db, create_tables, dispose_engine
from backend.models.user import User
from backend.models.ahorro import Ahorro
from backend.models.creditos import Credito
from backend.models.gastos_ingresos import GastoIngreso
from backend.models.deudas import Deuda
from backend.models.aportaciones import Aportacion
from backend.models.afore import Afore
from backend.models.gbm_portfolio import GbmPortfolio
from backend.models.categories import Category
from backend.models.instruments import Instrument
from backend.models.courses import Course, Lesson
from backend.models.lesson_progress import LessonProgress
from backend.models.conversation import ConversationSession
from backend.models.update_tracker import UpdateTracker

__all__ = [
    "Base",
    "engine",
    "async_session",
    "get_db",
    "create_tables",
    "dispose_engine",
    "User",
    "Ahorro",
    "Credito",
    "GastoIngreso",
    "Deuda",
    "Aportacion",
    "Afore",
    "GbmPortfolio",
    "Category",
    "Instrument",
    "Course",
    "Lesson",
    "LessonProgress",
    "ConversationSession",
    "UpdateTracker",
]
