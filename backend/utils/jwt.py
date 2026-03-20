"""
JWT令牌工具
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional

# JWT配置
SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
if not SECRET_KEY:
    # Fall back to a per-process random key so the repo never ships a shared signing secret.
    SECRET_KEY = secrets.token_urlsafe(32)
    print("WARNING: SECRET_KEY is not set; using an ephemeral key. Tokens will become invalid after restart.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天
CHINA_TZ = timezone(timedelta(hours=8))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(CHINA_TZ) + expires_delta
    else:
        expire = datetime.now(CHINA_TZ) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
