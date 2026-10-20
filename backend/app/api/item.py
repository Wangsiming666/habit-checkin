from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import AuthContext, get_auth
from app.common.response import ok
from app.db.mysql import get_db
from app.schemas.item import ItemCreateIn
from app.service import item_service

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("")
async def list_items(
    auth: AuthContext = Depends(get_auth),
    session: AsyncSession = Depends(get_db),
):
    return ok(await item_service.list_items(session, auth.user_id))


@router.post("")
async def create_item(
    body: ItemCreateIn,
    auth: AuthContext = Depends(get_auth),
    session: AsyncSession = Depends(get_db),
):
    return ok(await item_service.create_item(session, auth.user_id, body.item_name))
