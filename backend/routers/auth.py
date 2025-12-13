"""
认证路由 - 注册、登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
import secrets

from models.schemas import RegisterRequest, LoginRequest, TokenResponse
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token
from storage import JsonStorage

router = APIRouter()
storage = JsonStorage()

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    pwd_hash = hash_password(req.password)

    try:
        user = storage.register_user(req.username, pwd_hash, req.invite_code)
    except ValueError as e:
        if str(e) == "invalid_invite":
            raise HTTPException(status_code=400, detail="邀请码无效或已使用")
        if str(e) == "username_exists":
            raise HTTPException(status_code=400, detail="用户名已存在")
        raise HTTPException(status_code=500, detail="注册失败")
    
    # 创建JWT令牌
    token = create_access_token({"sub": str(user["id"]), "username": req.username})
    
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=req.username
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录"""
    user = storage.get_user_by_username(req.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 验证密码
    if not verify_password(req.password, user.get("pwd_hash", "")):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建JWT令牌
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"]
    )
