from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import AuthContext, get_auth
from app.common.response import ok
from app.db.mysql import get_db
from app.schemas.auth import LoginIn
from app.service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginIn, session: AsyncSession = Depends(get_db)):
    return ok(await auth_service.login(session, body.username, body.password))


@router.post("/logout")
async def logout(auth: AuthContext = Depends(get_auth)):
    await auth_service.logout(auth.token)
    return ok({})
