"""密码哈希：bcrypt（passlib 封装）。

注意：requirements.txt 锁定 bcrypt==4.0.1——
passlib 1.7.4 会读取 bcrypt.__about__，bcrypt>=4.1 已删除该属性，会报 AttributeError。
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)
