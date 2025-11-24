"""
用户路由 - 个人信息、头像上传
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlite3 import Connection
from pathlib import Path
import shutil
from typing import Optional

from database import get_db
from models.schemas import UserProfile
from utils.jwt import verify_token

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_current_user(authorization: str = Header(...)):
    """从JWT令牌获取当前用户"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    return int(payload["sub"])

@router.get("/profile", response_model=UserProfile)
async def get_profile(user_id: int = Depends(get_current_user), db: Connection = Depends(get_db)):
    """获取用户个人信息"""
    cursor = db.cursor()
    cursor.execute("SELECT id, username, avatar FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserProfile(
        id=user["id"],
        username=user["username"],
        avatar=user["avatar"] or ""
    )

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """上传用户头像"""
    # 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 保存文件
    file_ext = file.filename.split(".")[-1]
    file_path = UPLOAD_DIR / f"{user_id}.{file_ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 更新数据库
    avatar_url = f"/uploads/avatars/{user_id}.{file_ext}"
    cursor = db.cursor()
    cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar_url, user_id))
    db.commit()
    
    return {"avatar": avatar_url, "message": "头像上传成功"}
