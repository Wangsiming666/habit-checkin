"""MySQL 异步连接池（SQLAlchemy 2.x + aiomysql）。"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,   # 取连接前探活，避免 MySQL 8 小时空闲断连
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI 依赖：每个请求一个独立 Session，请求结束自动关闭。"""
    async with SessionLocal() as session:
        yield session
