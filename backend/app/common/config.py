"""应用配置：所有连接信息与密钥统一走环境变量（backend/.env），代码中不出现真实凭据。"""
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py 位于 backend/app/common/，向上三级即 backend/
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "habit"
    db_password: str = ""
    db_name: str = "habit_checkin"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0

    # 登录态 TTL：7 天（秒）。退出登录时主动删除，过期由 Redis 自动清理
    token_ttl_seconds: int = 604800

    app_host: str = "0.0.0.0"
    app_port: int = 8000

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def database_url(self) -> str:
        # aiomysql 异步方言；凭据做 URL 编码，避免特殊字符破坏连接串
        return (
            f"mysql+aiomysql://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
