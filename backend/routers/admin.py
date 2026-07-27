"""Admin routes — restricted to adriax45@gmail.com.

Provides endpoints to manage referral/signup links for instruments.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from backend.models.database import get_db
from backend.models.instruments import Instrument

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_UID = "TMti8ciOrQbO2n3soWErc1dILTo1"  # adriax45@gmail.com


def _is_admin(request: Request) -> bool:
    uid = getattr(request.state, "user_id", None)
    return uid == ADMIN_UID


@router.get("/instruments")
async def list_instruments(request: Request, db: AsyncSession = Depends(get_db)):
    """List instruments grouped by institution for link management (admin only)."""
    if not _is_admin(request):
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    result = await db.execute(
        text("""SELECT DISTINCT institution, 
                MAX(referral_link) as referral_link, 
                MAX(signup_link) as signup_link
                FROM instruments 
                WHERE instrument_type != 'cetes'
                GROUP BY institution 
                ORDER BY institution""")
    )
    items = []
    for row in result.fetchall():
        items.append({
            "institution": row[0],
            "referral_link": row[1] or "",
            "signup_link": row[2] or "",
        })
    return {"items": items}


class LinkUpdate(BaseModel):
    referral_link: Optional[str] = None
    signup_link: Optional[str] = None


@router.put("/instruments/{institution}/links")
async def update_instrument_links(institution: str, payload: LinkUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Update referral/signup links for ALL instruments of an institution (admin only)."""
    if not _is_admin(request):
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    if payload.referral_link is not None:
        await db.execute(
            text("UPDATE instruments SET referral_link = :link WHERE institution = :inst"),
            {"link": payload.referral_link, "inst": institution}
        )
    if payload.signup_link is not None:
        await db.execute(
            text("UPDATE instruments SET signup_link = :link WHERE institution = :inst"),
            {"link": payload.signup_link, "inst": institution}
        )
    await db.commit()
    return {"success": True}
