"""
聊天路由 - AI对话功能
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlite3 import Connection
import json
import asyncio
from datetime import datetime

from database import get_db
from models.schemas import ChatMessage, ChatResponse
from routers.user import get_current_user
from services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

@router.post("/send")
async def send_message(
    message: ChatMessage,
    user_id: int = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """发送聊天消息"""
    cursor = db.cursor()
    
    # 保存用户消息到历史
    cursor.execute(
        "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, "user", message.content)
    )
    db.commit()
    
    # 获取用户聊天历史
    cursor.execute(
        "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
        (user_id,)
    )
    history = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
    history.reverse()
    
    try:
        # 调用AI服务
        response = await ai_service.chat(history, user_id)
        
        # 保存AI回复到历史
        cursor.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, "assistant", response["content"])
        )
        db.commit()
        
        return ChatResponse(
            role="assistant",
            content=response["content"],
            sentences=response.get("sentences"),
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")

@router.get("/history")
async def get_history(
    limit: int = 50,
    user_id: int = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """获取聊天历史"""
    cursor = db.cursor()
    cursor.execute(
        "SELECT role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    
    history = []
    for row in cursor.fetchall():
        history.append({
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        })
    
    history.reverse()
    return {"history": history}
