"""
管理路由 - 用户管理、邀请码管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
import secrets

from database import get_db
from models.schemas import InviteCodeCreate, PasswordReset
from utils.password import hash_password
from routers.user import get_current_user

router = APIRouter()

# 简单的管理员检查（实际应该有更完善的角色系统）
def is_admin(user_id: int = Depends(get_current_user)):
    # TODO: 实现真实的管理员检查
    # 目前简单判断user_id为1是管理员
    if user_id != 1:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user_id

@router.get("/users")
async def list_users(
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """获取用户列表"""
    cursor = db.cursor()
    cursor.execute("SELECT id, username, avatar, created_at FROM users")
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row["id"],
            "username": row["username"],
            "avatar": row["avatar"],
            "created_at": row["created_at"]
        })
    
    return {"users": users}

@router.post("/create_invite")
async def create_invite_codes(
    req: InviteCodeCreate,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """创建邀请码"""
    cursor = db.cursor()
    codes = []
    
    for _ in range(req.count):
        code = secrets.token_urlsafe(16)
        cursor.execute("INSERT INTO invites (code) VALUES (?)", (code,))
        codes.append(code)
    
    db.commit()
    
    return {"codes": codes, "count": len(codes)}

@router.get("/invites")
async def list_invites(
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """获取邀请码列表"""
    cursor = db.cursor()
    cursor.execute("SELECT code, used, used_by, created_at FROM invites ORDER BY created_at DESC")
    
    invites = []
    for row in cursor.fetchall():
        invites.append({
            "code": row["code"],
            "used": bool(row["used"]),
            "used_by": row["used_by"],
            "created_at": row["created_at"]
        })
    
    return {"invites": invites}

@router.post("/reset_password")
async def reset_password(
    req: PasswordReset,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """重置用户密码"""
    cursor = db.cursor()
    
    # 检查用户是否存在
    cursor.execute("SELECT id FROM users WHERE id = ?", (req.user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新密码
    pwd_hash = hash_password(req.new_password)
    cursor.execute("UPDATE users SET pwd_hash = ? WHERE id = ?", (pwd_hash, req.user_id))
    db.commit()
    
    return {"message": "密码重置成功"}

@router.post("/push")
async def push_message(
    message: str,
    admin_id: int = Depends(is_admin)
):
    """推送系统消息（定时消息功能）"""
    # TODO: 实现推送逻辑
    return {"message": "推送功能开发中"}
