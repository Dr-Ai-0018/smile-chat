"""
配置路由 - 系统配置管理
"""
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
import json
from pydantic import BaseModel

from routers.admin import is_admin

router = APIRouter()

CONFIG_DIR = Path(__file__).parent.parent / "config"

class ContextConfig(BaseModel):
    max_messages: int
    max_tokens: int
    system_prompt_tokens: int
    reserve_tokens: int

@router.get("/context")
async def get_context_config(admin_id: int = Depends(is_admin)):
    """获取上下文配置"""
    config_file = CONFIG_DIR / "context_config.json"
    
    if not config_file.exists():
        return {
            "max_messages": 20,
            "max_tokens": 4000,
            "system_prompt_tokens": 100,
            "reserve_tokens": 1000
        }
    
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/context")
async def update_context_config(
    config: ContextConfig,
    admin_id: int = Depends(is_admin)
):
    """更新上下文配置"""
    config_file = CONFIG_DIR / "context_config.json"
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # 验证配置
    if config.max_messages < 1 or config.max_messages > 100:
        raise HTTPException(status_code=400, detail="消息条数必须在1-100之间")
    
    if config.max_tokens < 500 or config.max_tokens > 32000:
        raise HTTPException(status_code=400, detail="Token数必须在500-32000之间")
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
    
    return {"message": "配置更新成功", "config": config}

@router.get("/api")
async def get_api_config(admin_id: int = Depends(is_admin)):
    """获取API配置（隐藏密钥）"""
    config_file = CONFIG_DIR / "api_channels.json"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="配置文件不存在")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 隐藏API密钥
    if "primary" in config and "api_key" in config["primary"]:
        key = config["primary"]["api_key"]
        config["primary"]["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
    
    for backup in config.get("backup", []):
        if "api_key" in backup:
            key = backup["api_key"]
            backup["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
    
    return config
