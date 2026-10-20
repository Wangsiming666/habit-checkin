"""20 并发打卡验证：恰好 1 个成功、19 个 409，数据库仅有 1 条记录。

用法：python scripts/concurrency_check.py [base_url]
前置：后端已启动，init.sql 已导入。
"""
import asyncio
import os
import sys
import time

import httpx
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.mysql import engine  # noqa: E402

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
CONCURRENCY = 20


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        login = await client.post("/api/auth/login", json={"username": "demo", "password": "123456"})
        token = login.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        item_name = f"并发测试-{int(time.time())}"
        created = await client.post("/api/items", json={"item_name": item_name}, headers=headers)
        item_id = created.json()["data"]["id"]
        print(f"item_id={item_id} name={item_name}")

        responses = await asyncio.gather(
            *[client.post(f"/api/check/{item_id}", headers=headers) for _ in range(CONCURRENCY)]
        )
        codes = sorted(r.status_code for r in responses)
        success = codes.count(200)
        conflict = codes.count(409)
        print(f"status_codes={codes}")
        print(f"success={success} conflict={conflict}")

        async with engine.connect() as conn:
            count = (
                await conn.execute(
                    text("SELECT COUNT(*) FROM check_record WHERE item_id = :item_id"),
                    {"item_id": item_id},
                )
            ).scalar()
        print(f"db_record_count={count}")

        assert success == 1, f"expected exactly 1 success, got {success}"
        assert conflict == CONCURRENCY - 1, f"expected 19 conflicts, got {conflict}"
        assert count == 1, f"expected 1 db record, got {count}"
        print("CONCURRENCY_PASSED")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
