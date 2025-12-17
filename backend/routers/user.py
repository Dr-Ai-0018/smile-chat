"""
用户路由 - 个人信息、头像上传
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from pathlib import Path
import shutil
import time
from typing import Optional

from models.schemas import UserProfile
from utils.jwt import verify_token
from storage import JsonStorage

router = APIRouter()
storage = JsonStorage()

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
async def get_profile(user_id: int = Depends(get_current_user)):
    """获取用户个人信息"""
    user = storage.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserProfile(
        id=user.get("id"),
        username=user.get("username"),
        avatar=user.get("avatar") or ""
    )

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """上传用户头像"""
    # 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 保存文件
    file_ext = file.filename.split(".")[-1]

    old = storage.get_user_by_id(user_id) or {}
    old_avatar = old.get("avatar") or ""
    if isinstance(old_avatar, str) and old_avatar.startswith("/uploads/avatars/"):
        try:
            old_name = old_avatar.split("/uploads/avatars/", 1)[1]
            old_path = UPLOAD_DIR / old_name
            if old_path.exists():
                old_path.unlink()
        except Exception:
            pass

    version = int(time.time())
    file_path = UPLOAD_DIR / f"{user_id}_{version}.{file_ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 更新存储
    avatar_url = f"/uploads/avatars/{user_id}_{version}.{file_ext}"
    updated = storage.update_user(user_id, {"avatar": avatar_url})
    if not updated:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"avatar": avatar_url, "message": "头像上传成功"}
