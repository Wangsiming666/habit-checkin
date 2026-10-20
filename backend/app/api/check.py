from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import AuthContext, get_auth
from app.common.response import ok
from app.db.mysql import get_db
from app.service import check_service

router = APIRouter(prefix="/api/check", tags=["check"])


@router.post("/{item_id}")
async def check_in(
    item_id: int = Path(..., gt=0),
    auth: AuthContext = Depends(get_auth),
    session: AsyncSession = Depends(get_db),
):
    return ok(await check_service.check_in(session, auth.user_id, item_id))


@router.get("/streak/{item_id}")
async def get_streak(
    item_id: int = Path(..., gt=0),
    auth: AuthContext = Depends(get_auth),
    session: AsyncSession = Depends(get_db),
):
    return ok(await check_service.get_streak(session, auth.user_id, item_id))
