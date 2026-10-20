from pydantic import BaseModel, field_validator


class ItemCreateIn(BaseModel):
    item_name: str

    @field_validator("item_name")
    @classmethod
    def validate_item_name(cls, v: str) -> str:
        v = v.strip()
        if not 1 <= len(v) <= 20:
            raise ValueError("打卡项名称长度需为 1~20 个字符")
        return v
