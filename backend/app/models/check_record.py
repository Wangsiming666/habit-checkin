"""打卡记录表模型。

uk_item_date(item_id, check_date)：并发防重的物理兜底。
即使 Redis 锁失效、多 worker 同时写入，数据库也只允许一条记录。
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CheckRecord(Base):
    __tablename__ = "check_record"
    __table_args__ = (UniqueConstraint("item_id", "check_date", name="uk_item_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
