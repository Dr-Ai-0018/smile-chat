"""
AI聊天系统 - 后端主入口
FastAPI + JWT认证 + SQLite数据库
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from routers import auth, chat, user, memory, admin, image, config
from database import init_db
from utils.jwt import verify_token

# 初始化数据库
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Smile-Chat API",
    description="AI聊天系统后端API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(memory.router, prefix="/api/memory", tags=["记忆"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(image.router, prefix="/api/image", tags=["图片"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])

@app.get("/")
async def root():
    return {"message": "Smile-Chat API v1.0", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
