"""应用入口：CORS、请求日志、全局异常、统一返回。"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, check, item
from app.common.config import settings
from app.common.exceptions import AppException
from app.common.response import fail
from app.db.mysql import engine
from app.db.redis import redis_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("habit")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("habit-checkin api starting")
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(title="习惯打卡 API", version="1.0.0", lifespan=lifespan)

# CORS 白名单走环境变量，禁止 allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    cost_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s %.1fms", request.method, request.url.path, response.status_code, cost_ms)
    return response


@app.exception_handler(AppException)
async def handle_app_exception(_: Request, exc: AppException):
    return JSONResponse(status_code=exc.code, content=fail(exc.code, exc.msg))


@app.exception_handler(RequestValidationError)
async def handle_validation(_: Request, exc: RequestValidationError):
    # FastAPI 默认 422 会破坏统一返回结构，这里统一转换为 400
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(part) for part in first.get("loc", []))
    msg = first.get("msg", "参数错误")
    return JSONResponse(status_code=400, content=fail(400, f"参数错误：{loc} {msg}".strip()))


@app.exception_handler(StarletteHTTPException)
async def handle_http(_: Request, exc: StarletteHTTPException):
    # 已声明接口的可预期错误只允许使用 400/401/409/500；框架级错误收敛为 400
    code = exc.status_code if exc.status_code in (400, 401, 409, 500) else 400
    msg = exc.detail if isinstance(exc.detail, str) else "请求错误"
    return JSONResponse(status_code=code, content=fail(code, msg))


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("unhandled error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=fail(500, "服务器内部错误"))


app.include_router(auth.router)
app.include_router(item.router)
app.include_router(check.router)
