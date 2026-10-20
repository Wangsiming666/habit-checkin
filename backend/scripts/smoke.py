"""全链路冒烟脚本：真实 HTTP 请求，逐条打印统一返回结构。

用法：python scripts/smoke.py [base_url]
前置：后端已启动，init.sql 已导入（demo/123456）。
"""
import asyncio
import sys
import time

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
passed = 0


def show(name: str, response: httpx.Response) -> dict:
    global passed
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}
    print(f"[{name}] HTTP {response.status_code} -> {body}")
    passed += 1
    return body


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        body = show("1 登录", await client.post("/api/auth/login", json={"username": "demo", "password": "123456"}))
        assert body["code"] == 200, body
        token = body["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        show("2 打卡项列表（初始）", await client.get("/api/items", headers=headers))

        item_name = f"冒烟测试-{int(time.time())}"
        body = show("3 创建打卡项", await client.post("/api/items", json={"item_name": item_name}, headers=headers))
        assert body["code"] == 200, body
        item_id = body["data"]["id"]

        body = show("4 今日打卡", await client.post(f"/api/check/{item_id}", headers=headers))
        assert body["code"] == 200 and body["data"]["current_streak"] >= 1, body

        resp = await client.post(f"/api/check/{item_id}", headers=headers)
        body = show("5 重复打卡（预期 409）", resp)
        assert resp.status_code == 409 and body["code"] == 409, body

        body = show("6 列表（应显示已打卡与连续天数）", await client.get("/api/items", headers=headers))
        matched = [i for i in body["data"]["items"] if i["id"] == item_id]
        assert matched and matched[0]["today_checked"] is True and matched[0]["current_streak"] >= 1, body

        body = show("7 查询连续天数", await client.get(f"/api/check/streak/{item_id}", headers=headers))
        assert body["code"] == 200 and body["data"]["today_checked"] is True, body

        show("8 退出登录", await client.post("/api/auth/logout", headers=headers))

        resp = await client.get("/api/items", headers=headers)
        body = show("9 登出后访问（预期 401）", resp)
        assert resp.status_code == 401 and body["code"] == 401, body

        resp = await client.get("/api/items")
        body = show("10 无 token 访问（预期 401）", resp)
        assert resp.status_code == 401, body

        print(f"SMOKE_ALL_PASSED steps={passed}")


if __name__ == "__main__":
    asyncio.run(main())
