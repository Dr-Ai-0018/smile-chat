"""
AI聊天系统 - 后端主入口
FastAPI + JWT认证 + SQLite数据库
"""
import os
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn

from dotenv import load_dotenv

# 必须在导入 routers/AIService 之前加载 .env，否则配置会在 import 时读取不到
load_dotenv()

from routers import auth, chat, user, memory, admin, image, config, prompts, notices, checkin
from utils.jwt import verify_token
from utils.password import hash_password
from storage import JsonStorage
from services.weekly_cleanup_service import start_weekly_cleanup_scheduler, stop_weekly_cleanup_scheduler


DEFAULT_CORS_ALLOW_ORIGINS = []
DEFAULT_CORS_ALLOW_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_cors_options() -> dict:
    allow_origins = _split_env_list(os.getenv("CORS_ALLOW_ORIGINS")) or DEFAULT_CORS_ALLOW_ORIGINS
    allow_origin_regex = (os.getenv("CORS_ALLOW_ORIGIN_REGEX") or DEFAULT_CORS_ALLOW_ORIGIN_REGEX).strip() or None
    return {
        "allow_origins": allow_origins,
        "allow_origin_regex": allow_origin_regex,
    }


def _bootstrap_on_empty_data() -> None:
    storage = JsonStorage()
    users = storage.read_users()
    if users:
        return

    invites = storage.read_invites()
    has_unused_invite = any((not i.get("used")) for i in invites if isinstance(i, dict))

    if not has_unused_invite:
        configured = (os.getenv("INIT_ADMIN_INVITE_CODE") or "").strip()
        admin_code = configured or ("smile-admin-" + secrets.token_urlsafe(8))
        while True:
            created = storage.create_invite_codes([admin_code])
            if created:
                break
            admin_code = "smile-admin-" + secrets.token_urlsafe(8)

        print("\n=== Bootstrap ===")
        print(f"✓ 已生成管理员邀请码: {admin_code}")
        print("提示：第一个注册的用户(ID=1)将拥有管理员权限。")
        print("可选：在环境变量中设置 INIT_ADMIN_USERNAME / INIT_ADMIN_PASSWORD 以自动创建管理员账号。")
        print("=================\n")
    else:
        admin_code = None

    username = (os.getenv("INIT_ADMIN_USERNAME") or "").strip()
    password = (os.getenv("INIT_ADMIN_PASSWORD") or "").strip()
    if username and password:
        if admin_code is None:
            # 尝试复用任意一个可用邀请码
            for i in storage.read_invites():
                if isinstance(i, dict) and (not i.get("used")) and i.get("code"):
                    admin_code = str(i.get("code"))
                    break

        if admin_code:
            try:
                storage.register_user(username, hash_password(password), admin_code)
                print("\n=== Bootstrap ===")
                print(f"✓ 已自动创建管理员账号: {username} (ID=1)")
                print("=================\n")
            except ValueError as e:
                print(f"\nBootstrap 创建管理员账号失败: {e}\n")

# 初始化数据库
@asynccontextmanager
async def lifespan(app: FastAPI):
    if (os.getenv("BOOTSTRAP_ON_STARTUP", "1").strip().lower() not in {"0", "false", "no"}):
        _bootstrap_on_empty_data()
    start_weekly_cleanup_scheduler()
    yield
    await stop_weekly_cleanup_scheduler()

app = FastAPI(
    title="Smile-Chat API",
    description="AI聊天系统后端API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
cors_options = _get_cors_options()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_options["allow_origins"],
    allow_origin_regex=cors_options["allow_origin_regex"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(memory.router, prefix="/api/memory", tags=["记忆"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(image.router, prefix="/api/image", tags=["图片"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])
app.include_router(prompts.router, prefix="/api", tags=["提示系统"])
app.include_router(notices.router, prefix="/api", tags=["通知系统"])
app.include_router(checkin.router, prefix="/api", tags=["打卡系统"])

# 静态文件服务 - 头像和图片上传
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
(UPLOADS_DIR / "avatars").mkdir(exist_ok=True)
(UPLOADS_DIR / "latest").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/avatars", StaticFiles(directory=str(UPLOADS_DIR / "avatars")), name="avatars")

@app.middleware("http")
async def add_static_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/uploads/avatars/") or request.url.path.startswith("/avatars/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

@app.get("/")
async def root():
    return {"message": "Smile-Chat API v1.0", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
