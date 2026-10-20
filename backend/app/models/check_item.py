"""打卡项表模型。

uk_user_item(user_id, item_name)：同一用户下名称唯一；
该联合索引的最左前缀天然覆盖按 user_id 的查询，无需再建单列索引。
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CheckItem(Base):
    __tablename__ = "check_item"
    __table_args__ = (UniqueConstraint("user_id", "item_name", name="uk_user_item"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    create_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
