"""
管理路由 - 用户管理、邀请码管理、查看用户数据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from pathlib import Path
from pydantic import BaseModel
import secrets
import json

from database import get_db
from models.schemas import InviteCodeCreate, PasswordReset
from utils.password import hash_password
from routers.user import get_current_user

router = APIRouter()

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
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """获取用户列表"""
    cursor = db.cursor()
    cursor.execute("SELECT id, username, avatar, created_at FROM users")
    
    users = []
    for row in cursor.fetchall():
        # 获取用户消息数量
        cursor.execute("SELECT COUNT(*) as count FROM chat_history WHERE user_id = ?", (row["id"],))
        msg_count = cursor.fetchone()["count"]
        
        users.append({
            "id": row["id"],
            "username": row["username"],
            "avatar": row["avatar"],
            "created_at": row["created_at"],
            "message_count": msg_count
        })
    
    return {"users": users}

@router.get("/user/{user_id}/history")
async def get_user_history(
    user_id: int,
    limit: int = 100,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """查看指定用户的聊天记录（管理员权限）"""
    cursor = db.cursor()
    
    # 检查用户是否存在
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查image列是否存在
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'image' in columns:
        cursor.execute(
            "SELECT id, role, content, image, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "image": row["image"],
                "timestamp": row["timestamp"]
            })
    else:
        cursor.execute(
            "SELECT id, role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "image": None,
                "timestamp": row["timestamp"]
            })
    
    history.reverse()
    return {
        "user_id": user_id,
        "username": user["username"],
        "history": history
    }

@router.get("/user/{user_id}/memory")
async def get_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """查看指定用户的记忆（管理员权限）"""
    cursor = db.cursor()
    
    # 检查用户是否存在
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    memory_data = {
        "long_term": "",
        "json_memory": {},
        "history_files": []
    }
    
    # 读取长期记忆
    long_term_file = memory_dir / "memory" / "long_term.txt"
    if long_term_file.exists():
        memory_data["long_term"] = long_term_file.read_text(encoding="utf-8")
    
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
        "username": user["username"],
        "memory": memory_data
    }

@router.delete("/user/{user_id}/history")
async def clear_user_history(
    user_id: int,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """清空指定用户的聊天记录（管理员权限）"""
    cursor = db.cursor()
    
    # 检查用户是否存在
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="用户不存在")
    
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    db.commit()
    
    return {"message": f"用户 {user_id} 的聊天记录已清空"}

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
    """推送系统消息"""
    # TODO: 实现推送逻辑
    return {"message": "推送功能开发中"}

@router.get("/memory/all")
async def list_all_memory(
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """列出所有用户的记忆状态"""
    cursor = db.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    
    memory_list = []
    for user in users:
        user_id = user["id"]
        username = user["username"]
        memory_dir = MEMORY_BASE_PATH / str(user_id)
        
        user_memory = {
            "user_id": user_id,
            "username": username,
            "has_long_term": False,
            "has_json": False,
            "history_count": 0,
            "long_term_preview": ""
        }
        
        # 检查长期记忆
        long_term_file = memory_dir / "memory" / "long_term.txt"
        if long_term_file.exists():
            content = long_term_file.read_text(encoding="utf-8").strip()
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
    db: Connection = Depends(get_db)
):
    """更新用户长期记忆"""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id) / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    long_term_file = memory_dir / "long_term.txt"
    long_term_file.write_text(request.content, encoding="utf-8")
    
    return {"message": "记忆更新成功"}

@router.delete("/user/{user_id}/memory")
async def clear_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """清空用户所有记忆"""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    
    import shutil
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
    
    # 重新创建空目录结构
    (memory_dir / "history").mkdir(parents=True, exist_ok=True)
    (memory_dir / "json").mkdir(parents=True, exist_ok=True)
    (memory_dir / "memory").mkdir(parents=True, exist_ok=True)
    
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
    db: Connection = Depends(get_db)
):
    """删除用户及其所有数据"""
    if user_id == 1:
        raise HTTPException(status_code=403, detail="不能删除管理员")
    
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除聊天记录
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    # 删除用户
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    
    # 删除记忆文件
    import shutil
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
    
    return {"message": "用户已删除"}

@router.get("/stats")
async def get_system_stats(
    admin_id: int = Depends(is_admin),
    db: Connection = Depends(get_db)
):
    """获取系统统计数据"""
    cursor = db.cursor()
    
    # 用户总数
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    
    # 消息总数
    cursor.execute("SELECT COUNT(*) as count FROM chat_history")
    msg_count = cursor.fetchone()["count"]
    
    # 今日消息数
    cursor.execute("""
        SELECT COUNT(*) as count FROM chat_history 
        WHERE date(timestamp) = date('now')
    """)
    today_msg_count = cursor.fetchone()["count"]
    
    # 活跃用户（今天有消息的用户）
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM chat_history
        WHERE date(timestamp) = date('now')
    """)
    active_users = cursor.fetchone()["count"]
    
    # 可用邀请码
    cursor.execute("SELECT COUNT(*) as count FROM invites WHERE used = 0")
    available_invites = cursor.fetchone()["count"]
    
    return {
        "user_count": user_count,
        "message_count": msg_count,
        "today_messages": today_msg_count,
        "active_users_today": active_users,
        "available_invites": available_invites
    }