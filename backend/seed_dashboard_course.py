"""Insert the 'Domina tu Dashboard' course into the database."""

import asyncio

from sqlalchemy import select

from backend.models.courses import Course, Lesson
from backend.models.database import async_session
from backend.seed_courses import LESSON_CONTENT

COURSE_DATA = {
    "id": "domina-tu-dashboard",
    "title": "Domina tu Dashboard Financiero",
    "description": "Aprende a usar cada sección del dashboard: patrimonio neto, gastos, créditos, inversiones, deudas y aportaciones.",
    "sort_order": 4,
    "lessons": [
        {"id": "dash-intro", "title": "¿Qué es el Dashboard?", "sort_order": 1},
        {"id": "dash-patrimonio", "title": "Patrimonio neto y tasa de ahorro", "sort_order": 2},
        {"id": "dash-gastos-ingresos", "title": "Gastos e Ingresos", "sort_order": 3},
        {"id": "dash-creditos", "title": "Tarjetas de crédito", "sort_order": 4},
        {"id": "dash-deudas", "title": "Deudas y préstamos", "sort_order": 5},
        {"id": "dash-inversiones", "title": "Inversiones y ahorro", "sort_order": 6},
        {"id": "dash-aportaciones", "title": "Aportaciones periódicas", "sort_order": 7},
    ],
}


async def main():
    async with async_session() as db:
        result = await db.execute(select(Course).where(Course.id == COURSE_DATA["id"]))
        if result.scalars().first():
            print("Course already exists. Skipping.")
            return

        course = Course(
            id=COURSE_DATA["id"],
            title=COURSE_DATA["title"],
            description=COURSE_DATA["description"],
            lesson_count=len(COURSE_DATA["lessons"]),
            sort_order=COURSE_DATA["sort_order"],
        )
        db.add(course)

        for lesson_data in COURSE_DATA["lessons"]:
            content = LESSON_CONTENT.get(lesson_data["id"], "<p>Contenido en desarrollo</p>")
            lesson = Lesson(
                id=lesson_data["id"],
                course_id=COURSE_DATA["id"],
                title=lesson_data["title"],
                content=content,
                sort_order=lesson_data["sort_order"],
            )
            db.add(lesson)

        await db.commit()
        print(f"Course inserted with {len(COURSE_DATA['lessons'])} lessons.")


if __name__ == "__main__":
    asyncio.run(main())
