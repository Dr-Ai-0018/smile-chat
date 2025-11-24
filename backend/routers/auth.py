"""
认证路由 - 注册、登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
import secrets

from database import get_db
from models.schemas import RegisterRequest, LoginRequest, TokenResponse
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: Connection = Depends(get_db)):
    """用户注册"""
    cursor = db.cursor()
    
    # 检查邀请码
    cursor.execute("SELECT * FROM invites WHERE code = ? AND used = 0", (req.invite_code,))
    invite = cursor.fetchone()
    if not invite:
        raise HTTPException(status_code=400, detail="邀请码无效或已使用")
    
    # 检查用户名是否存在
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    pwd_hash = hash_password(req.password)
    cursor.execute(
        "INSERT INTO users (username, pwd_hash, invite_code_used) VALUES (?, ?, ?)",
        (req.username, pwd_hash, req.invite_code)
    )
    user_id = cursor.lastrowid
    
    # 标记邀请码已使用
    cursor.execute("UPDATE invites SET used = 1, used_by = ? WHERE code = ?", 
                  (user_id, req.invite_code))
    
    db.commit()
    
    # 创建JWT令牌
    token = create_access_token({"sub": str(user_id), "username": req.username})
    
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=req.username
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Connection = Depends(get_db)):
    """用户登录"""
    cursor = db.cursor()
    
    # 查找用户
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 验证密码
    if not verify_password(req.password, user["pwd_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建JWT令牌
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"]
    )
