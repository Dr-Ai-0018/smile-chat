"""
Pydantic数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 认证相关
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)
    invite_code: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

# 聊天相关
class ChatMessage(BaseModel):
    content: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    sentences: Optional[List[str]] = None
    timestamp: datetime
    reply: Optional[str] = None
    segments: Optional[List[str]] = None
    meta: Optional[dict] = None

# 用户相关
class UserProfile(BaseModel):
    id: int
    username: str
    avatar: str

# 记忆相关
class MemoryUpdate(BaseModel):
    user_id: int
    content: str
    memory_type: str  # "history", "json", "memory"

# 管理相关
class InviteCodeCreate(BaseModel):
    count: int = 1

class PasswordReset(BaseModel):
    user_id: int
    new_password: str
