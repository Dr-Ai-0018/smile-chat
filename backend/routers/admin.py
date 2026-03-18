"""
管理路由 - 用户管理、邀请码管理、查看用户数据
"""
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
from pydantic import BaseModel
from typing import List
import os
import secrets
import json
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)

from models.schemas import InviteCodeCreate, PasswordReset
from pydantic import BaseModel as PydanticBaseModel
from utils.password import hash_password
from routers.user import get_current_user
from storage import JsonStorage
from services.memory_service import get_memory_service

router = APIRouter()
storage = JsonStorage()
memory_service = get_memory_service()

MEMORY_BASE_PATH = Path(__file__).parent.parent.parent / "memory" / "本体"

# 管理员检查
def is_admin(user_id: int = Depends(get_current_user)):
    # 简单判断user_id为1是管理员
    # TODO: 实现更完善的角色系统
    if user_id != 1:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user_id

@router.get("/users")
async def list_users(
    admin_id: int = Depends(is_admin)
):
    """获取用户列表"""
    users = []
    for user in storage.read_users():
        user_id = user.get("id")
        if not isinstance(user_id, int):
            continue

        msg_count = storage.count_chat_messages(user_id)
        state = storage.get_user_experiment_state(user_id)
        users.append({
            "id": user_id,
            "username": user.get("username"),
            "avatar": user.get("avatar"),
            "created_at": user.get("created_at"),
            "message_count": msg_count,
            "condition": user.get("self_disclosure_condition", "none"),
            "weekly_checkin_count": state.get("weekly_checkin_count", 0),
        })

    return {
        "users": users,
        "threshold": MIN_WEEKLY_CHECKINS_FOR_SURVEY,
    }

@router.get("/user/{user_id}/history")
async def get_user_history(
    user_id: int,
    limit: int = 100,
    admin_id: int = Depends(is_admin)
):
    """查看指定用户的聊天记录（管理员权限）"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    history = storage.get_chat_history(user_id=user_id, limit=limit)
    return {
        "user_id": user_id,
        "username": user.get("username"),
        "history": history
    }

@router.get("/user/{user_id}/memory")
async def get_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """查看指定用户的记忆（管理员权限）"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    memory_data = {
        "long_term": "",
        "json_memory": {},
        "history_files": []
    }
    
    # 读取长期记忆（通过MemoryService）
    memory_data["long_term"] = memory_service.read_ltm_text(user_id)
    
    # 读取JSON记忆
    json_file = memory_dir / "json" / "memory.json"
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                memory_data["json_memory"] = json.load(f)
        except:
            pass
    
    # 列出历史文件
    history_dir = memory_dir / "history"
    if history_dir.exists():
        for file in sorted(history_dir.glob("*.txt"), reverse=True)[:10]:
            memory_data["history_files"].append({
                "name": file.name,
                "content": file.read_text(encoding="utf-8")[:500] + "..."
            })
    
    return {
        "user_id": user_id,
        "username": user.get("username"),
        "memory": memory_data
    }

@router.delete("/user/{user_id}/history")
async def clear_user_history(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """清空指定用户的聊天记录（管理员权限）"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    storage.clear_chat_history(user_id)
    
    return {"message": f"用户 {user_id} 的聊天记录已清空"}

@router.post("/create_invite")
async def create_invite_codes(
    req: InviteCodeCreate,
    admin_id: int = Depends(is_admin),
):
    """创建邀请码"""
    created: List[dict] = []
    remaining = max(0, int(req.count))

    while remaining > 0:
        batch = [secrets.token_urlsafe(16) for _ in range(remaining)]
        created_batch = storage.create_invite_codes(batch)
        created.extend(created_batch)
        remaining = req.count - len(created)

    codes = [c.get("code") for c in created if c.get("code")]
    return {"codes": codes, "count": len(codes)}

@router.get("/invites")
async def list_invites(
    admin_id: int = Depends(is_admin),
):
    """获取邀请码列表"""
    invites = storage.read_invites()
    invites.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    formatted = []
    for invite in invites:
        formatted.append({
            "code": invite.get("code"),
            "used": bool(invite.get("used")),
            "used_by": invite.get("used_by"),
            "created_at": invite.get("created_at")
        })

    return {"invites": formatted}

@router.post("/reset_password")
async def reset_password(
    req: PasswordReset,
    admin_id: int = Depends(is_admin),
):
    """重置用户密码"""
    if not storage.get_user_by_id(req.user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    pwd_hash = hash_password(req.new_password)
    storage.update_user(req.user_id, {"pwd_hash": pwd_hash})
    
    return {"message": "密码重置成功"}

@router.post("/push")
async def push_message(
    message: str,
    admin_id: int = Depends(is_admin)
):
    """推送系统消息"""
    # TODO: 实现推送逻辑
    return {"message": "推送功能开发中"}

@router.get("/memory/all")
async def list_all_memory(
    admin_id: int = Depends(is_admin),
):
    """列出所有用户的记忆状态"""
    memory_list = []
    for user in storage.read_users():
        user_id = user.get("id")
        username = user.get("username")
        if not isinstance(user_id, int):
            continue
        memory_dir = MEMORY_BASE_PATH / str(user_id)
        
        user_memory = {
            "user_id": user_id,
            "username": username,
            "has_long_term": False,
            "has_json": False,
            "history_count": 0,
            "long_term_preview": ""
        }
        
        # 检查长期记忆（通过MemoryService）
        content = memory_service.read_ltm_text(user_id).strip()
        if content:
            user_memory["has_long_term"] = True
            user_memory["long_term_preview"] = content[:200] + "..." if len(content) > 200 else content
        
        # 检查JSON记忆
        json_file = memory_dir / "json" / "memory.json"
        if json_file.exists():
            user_memory["has_json"] = True
        
        # 统计历史文件数
        history_dir = memory_dir / "history"
        if history_dir.exists():
            user_memory["history_count"] = len(list(history_dir.glob("*.txt")))
        
        memory_list.append(user_memory)
    
    return {"memories": memory_list}

class MemoryUpdateRequest(BaseModel):
    content: str

@router.put("/user/{user_id}/memory/long_term")
async def update_user_long_term_memory(
    user_id: int,
    request: MemoryUpdateRequest,
    admin_id: int = Depends(is_admin),
):
    """更新用户长期记忆"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_service.write_ltm(user_id, request.content, {"admin_edit": True})
    
    return {"message": "记忆更新成功"}

@router.delete("/user/{user_id}/memory")
async def clear_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """清空用户所有记忆"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    
    import shutil
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
    
    # 重新创建空目录结构
    (memory_dir / "history").mkdir(parents=True, exist_ok=True)
    (memory_dir / "json").mkdir(parents=True, exist_ok=True)
    (memory_dir / "memory").mkdir(parents=True, exist_ok=True)
    (memory_dir / "ltm").mkdir(parents=True, exist_ok=True)
    
    return {"message": "记忆已清空"}

@router.get("/user/{user_id}/history_file/{filename}")
async def get_history_file(
    user_id: int,
    filename: str,
    admin_id: int = Depends(is_admin)
):
    """获取指定历史文件的完整内容"""
    history_file = MEMORY_BASE_PATH / str(user_id) / "history" / filename
    if not history_file.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"content": history_file.read_text(encoding="utf-8")}

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """删除用户及其所有数据"""
    if user_id == 1:
        raise HTTPException(status_code=403, detail="不能删除管理员")

    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    storage.clear_chat_history(user_id)
    storage.delete_user(user_id)
    
    # 删除记忆文件
    import shutil
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
    
    return {"message": "用户已删除"}

@router.get("/stats")
async def get_system_stats(
    admin_id: int = Depends(is_admin),
):
    """获取系统统计数据"""

    users = storage.read_users()
    user_count = len(users)

    today = get_china_now().date()
    msg_count = 0
    today_msg_count = 0
    active_users = 0
    for user in users:
        uid = user.get("id")
        if not isinstance(uid, int):
            continue

        history = storage.get_chat_history(user_id=uid, limit=0)
        msg_count += len(history)

        has_today = False
        for item in history:
            ts = item.get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                continue
            if dt.date() == today:
                today_msg_count += 1
                has_today = True
        if has_today:
            active_users += 1

    available_invites = sum(1 for i in storage.read_invites() if not i.get("used"))
    
    return {
        "user_count": user_count,
        "message_count": msg_count,
        "today_messages": today_msg_count,
        "active_users_today": active_users,
        "available_invites": available_invites
    }

# ==================== 邀请码开关 ====================
class InviteCodeToggleRequest(PydanticBaseModel):
    enabled: bool

@router.get("/settings/invite_code")
async def get_invite_code_setting(
    admin_id: int = Depends(is_admin),
):
    """获取邀请码开关状态"""
    settings = storage.get_settings()
    return {
        "invite_code_enabled": settings.get("invite_code_enabled", True)
    }

@router.post("/settings/invite_code")
async def set_invite_code_setting(
    req: InviteCodeToggleRequest,
    admin_id: int = Depends(is_admin),
):
    """设置邀请码开关状态"""
    settings = storage.update_settings({"invite_code_enabled": req.enabled})
    return {
        "invite_code_enabled": settings.get("invite_code_enabled", True),
        "message": "邀请码已" + ("启用" if req.enabled else "关闭")
    }

# ==================== 通用设置 GET/PUT ====================
@router.get("/settings")
async def get_all_settings(admin_id: int = Depends(is_admin)):
    """获取所有系统设置"""
    return storage.get_settings()

@router.put("/settings")
async def update_all_settings(
    updates: dict,
    admin_id: int = Depends(is_admin),
):
    """更新系统设置（部分更新）"""
    # 校验打卡题目数量
    if "checkin_questions" in updates:
        qs = updates["checkin_questions"]
        if not isinstance(qs, list) or len(qs) == 0:
            raise HTTPException(status_code=400, detail="打卡题目至少需要1题")
        updates["checkin_questions"] = [q for q in qs if isinstance(q, str) and q.strip()]
        if len(updates["checkin_questions"]) == 0:
            raise HTTPException(status_code=400, detail="打卡题目不能全为空")
    settings = storage.update_settings(updates)
    return settings


# ==================== 打卡相关 ====================
MIN_WEEKLY_CHECKINS_FOR_SURVEY = int(os.getenv("MIN_WEEKLY_CHECKINS_FOR_SURVEY", "2"))

@router.get("/checkin/incomplete")
async def get_incomplete_checkin_users(
    admin_id: int = Depends(is_admin),
):
    """获取本周未完成打卡的用户列表（weekly_checkin_count < 阈值）"""
    result = []
    for user in storage.read_users():
        user_id = user.get("id")
        if not isinstance(user_id, int):
            continue
        state = storage.get_user_experiment_state(user_id)
        weekly_count = state.get("weekly_checkin_count", 0)
        if weekly_count < MIN_WEEKLY_CHECKINS_FOR_SURVEY:
            result.append({
                "id": user_id,
                "username": user.get("username"),
                "weekly_checkin_count": weekly_count,
                "required": MIN_WEEKLY_CHECKINS_FOR_SURVEY,
            })
    return {
        "users": result,
        "threshold": MIN_WEEKLY_CHECKINS_FOR_SURVEY,
        "total": len(result),
    }
