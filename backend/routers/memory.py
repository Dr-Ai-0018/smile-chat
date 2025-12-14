"""
记忆路由 - 基于文件的记忆系统
"""
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
import json
from datetime import datetime

from routers.user import get_current_user
from models.schemas import MemoryUpdate
from services.ai_service import AIService
from services.memory_service import get_memory_service

ai_service = AIService()
memory_service = get_memory_service()

router = APIRouter()

MEMORY_DIR = Path(__file__).parent.parent.parent / "memory" / "本体"

def get_user_memory_dir(user_id: int) -> Path:
    """获取用户记忆目录"""
    user_dir = MEMORY_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

@router.get("/{user_id}")
async def get_memory(
    user_id: int,
    current_user: int = Depends(get_current_user)
):
    """获取用户记忆"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="无权访问")
    
    memory_dir = get_user_memory_dir(user_id)
    
    # 读取三种记忆类型
    memory_data = {
        "history": [],
        "json": {},
        "memory": []
    }
    
    # 历史记录
    history_dir = memory_dir / "history"
    if history_dir.exists():
        for file in history_dir.glob("*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                memory_data["history"].append({
                    "file": file.name,
                    "content": f.read()
                })
    
    # JSON记忆
    json_file = memory_dir / "json" / "memory.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            memory_data["json"] = json.load(f)
    
    # 长期记忆
    ltm_text = memory_service.read_ltm_text(user_id)
    if ltm_text:
        memory_data["memory"] = ltm_text.split("\n\n")
    
    return memory_data

@router.post("/update")
async def update_memory(
    update: MemoryUpdate,
    current_user: int = Depends(get_current_user)
):
    """更新用户记忆"""
    if current_user != update.user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    memory_dir = get_user_memory_dir(update.user_id)
    
    if update.memory_type == "history":
        # 保存历史记录
        history_dir = memory_dir / "history"
        history_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = history_dir / f"{timestamp}.txt"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(update.content)
    
    elif update.memory_type == "json":
        # 更新JSON记忆
        json_dir = memory_dir / "json"
        json_dir.mkdir(exist_ok=True)
        
        json_file = json_dir / "memory.json"
        
        try:
            content = json.loads(update.content)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="无效的JSON格式")
    
    elif update.memory_type == "memory":
        # 更新长期记忆（通过MemoryService，带版本管理）
        existing = memory_service.read_ltm_text(update.user_id)
        if existing and update.content:
            merged = existing.rstrip() + "\n\n" + update.content
        else:
            merged = update.content
        memory_service.write_ltm(update.user_id, merged, {"manual_update": True})
    
    else:
        raise HTTPException(status_code=400, detail="无效的记忆类型")
    
    return {"message": "记忆更新成功"}

@router.post("/compress")
async def compress_memory(
    user_id: int,
    current_user: int = Depends(get_current_user)
):
    """手动压缩记忆（调用外部AI）"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    try:
        result = await ai_service.compress_memory(user_id)
        return {"message": "记忆压缩成功", "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记忆压缩失败: {str(e)}")
