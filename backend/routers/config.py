"""
配置路由 - 系统配置管理
"""
from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
import json
import os
from pydantic import BaseModel, Field

from routers.admin import is_admin

router = APIRouter()

CONFIG_DIR = Path(__file__).parent.parent / "config"
DEFAULT_CONTEXT_CONFIG = {
    "max_messages": 80,
    "max_tokens": 12000,
    "system_prompt_tokens": 100,
    "reserve_tokens": 1000,
    "image_rounds": 5,
}
DEFAULT_API_CONFIG = {
    "primary": {
        "name_env": "AI_PRIMARY_NAME",
        "base_url_env": "AI_PRIMARY_BASE_URL",
        "model_env": "AI_PRIMARY_MODEL",
        "api_key_env": "AI_PRIMARY_KEY",
        "api_type": "openai",
        "price": "",
    },
    "backup": [
        {
            "name_env": "AI_BACKUP_NAME",
            "base_url_env": "AI_BACKUP_BASE_URL",
            "api_key_env": "AI_BACKUP_KEY",
            "model_env": "AI_BACKUP_MODEL",
            "api_type": "openai",
            "price": "",
        }
    ],
    "enable_search": True,
    "max_context_messages": 80,
    "image_context_rounds": 5,
}


class ContextConfig(BaseModel):
    max_messages: int
    max_tokens: int
    system_prompt_tokens: int
    reserve_tokens: int
    image_rounds: int = 5


class ApiChannelConfig(BaseModel):
    name: str = ""
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    name_env: str = ""
    base_url_env: str = ""
    model_env: str = ""
    api_key_env: str = ""
    api_type: str = "openai"
    price: str = ""


class ApiConfigPayload(BaseModel):
    primary: ApiChannelConfig
    backup: list[ApiChannelConfig] = Field(default_factory=list)
    enable_search: bool = True
    max_context_messages: int = 80
    image_context_rounds: int = 5


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return deepcopy(default)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        merged = deepcopy(default)
        merged.update(raw)
        return merged
    return deepcopy(default)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_context_config_file() -> dict:
    return _read_json(CONFIG_DIR / "context_config.json", DEFAULT_CONTEXT_CONFIG)


def _api_config_file() -> Path:
    return CONFIG_DIR / "api_channels.json"


def _load_api_config_file() -> dict:
    config = _read_json(_api_config_file(), DEFAULT_API_CONFIG)
    if not isinstance(config.get("primary"), dict):
        config["primary"] = deepcopy(DEFAULT_API_CONFIG["primary"])
    backups = config.get("backup")
    if not isinstance(backups, list):
        config["backup"] = []
    return config


def _resolve_channel(channel: dict) -> tuple[dict, dict]:
    raw = dict(channel or {})
    resolved = dict(raw)
    override_flags = {}

    mapping = (
        ("name", "name_env"),
        ("base_url", "base_url_env"),
        ("model", "model_env"),
    )
    for value_key, env_key in mapping:
        env_var = (raw.get(env_key) or "").strip()
        env_val = (os.getenv(env_var) or "").strip() if env_var else ""
        if env_val:
            resolved[value_key] = env_val
            override_flags[value_key] = True
        else:
            override_flags[value_key] = False

    api_key_env_var = (raw.get("api_key_env") or "").strip()
    api_key_from_env = (os.getenv(api_key_env_var) or "").strip() if api_key_env_var else ""
    if api_key_from_env:
        resolved["api_key"] = api_key_from_env
        override_flags["api_key"] = True
    else:
        override_flags["api_key"] = False

    return resolved, override_flags


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _serialize_api_channel(channel: dict, *, mask_secret: bool) -> dict:
    data = dict(channel or {})
    api_key = data.get("api_key")
    data["api_key_masked"] = _mask_secret(api_key or "")
    data["has_api_key"] = bool(api_key)
    data["api_key"] = ""
    return data


def _merge_channel(existing: dict, incoming: dict) -> dict:
    merged = dict(existing or {})
    merged.update(incoming or {})

    incoming_key = (incoming or {}).get("api_key")
    if isinstance(incoming_key, str):
        if incoming_key.strip():
            merged["api_key"] = incoming_key.strip()
        else:
            merged["api_key"] = (existing or {}).get("api_key", "")

    return merged


def _build_api_config_response() -> dict:
    stored = _load_api_config_file()
    effective = deepcopy(stored)
    overrides = {"primary": {}, "backup": []}

    effective["primary"], overrides["primary"] = _resolve_channel(stored.get("primary", {}))
    effective_backups = []
    for backup in stored.get("backup", []):
        resolved, flags = _resolve_channel(backup if isinstance(backup, dict) else {})
        effective_backups.append(resolved)
        overrides["backup"].append(flags)
    effective["backup"] = effective_backups

    return {
        "stored": {
            "primary": _serialize_api_channel(stored.get("primary", {}), mask_secret=False),
            "backup": [
                _serialize_api_channel(item if isinstance(item, dict) else {}, mask_secret=False)
                for item in stored.get("backup", [])
            ],
            "enable_search": bool(stored.get("enable_search", True)),
            "max_context_messages": int(stored.get("max_context_messages", 80) or 80),
            "image_context_rounds": int(stored.get("image_context_rounds", 5) or 5),
        },
        "effective": {
            "primary": _serialize_api_channel(effective.get("primary", {}), mask_secret=True),
            "backup": [
                _serialize_api_channel(item if isinstance(item, dict) else {}, mask_secret=True)
                for item in effective.get("backup", [])
            ],
            "enable_search": bool(effective.get("enable_search", True)),
            "max_context_messages": int(effective.get("max_context_messages", 80) or 80),
            "image_context_rounds": int(effective.get("image_context_rounds", 5) or 5),
        },
        "env_overrides": overrides,
    }

@router.get("/context")
async def get_context_config(admin_id: int = Depends(is_admin)):
    """获取上下文配置"""
    return _load_context_config_file()

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

    if config.system_prompt_tokens < 50 or config.system_prompt_tokens > 2000:
        raise HTTPException(status_code=400, detail="系统提示Token必须在50-2000之间")

    if config.reserve_tokens < 100 or config.reserve_tokens > 8000:
        raise HTTPException(status_code=400, detail="保留Token必须在100-8000之间")

    if config.image_rounds < 1 or config.image_rounds > 20:
        raise HTTPException(status_code=400, detail="图片轮次必须在1-20之间")

    payload = _load_context_config_file()
    payload.update(config.model_dump())
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    return {"message": "配置更新成功", "config": payload}

@router.get("/api")
async def get_api_config(admin_id: int = Depends(is_admin)):
    """获取API配置（同时返回存储值与当前生效值）"""
    return _build_api_config_response()


@router.put("/api")
async def update_api_config(
    payload: ApiConfigPayload,
    admin_id: int = Depends(is_admin),
):
    """更新 API 通道配置"""
    data = payload.model_dump()
    existing = _load_api_config_file()
    merged = deepcopy(existing)

    primary = _merge_channel(existing.get("primary", {}), data.get("primary") or {})
    merged["primary"] = primary
    if not (primary.get("base_url") or primary.get("base_url_env")):
        raise HTTPException(status_code=400, detail="主通道必须配置 base_url 或 base_url_env")
    if not (primary.get("model") or primary.get("model_env")):
        raise HTTPException(status_code=400, detail="主通道必须配置 model 或 model_env")
    if not (primary.get("api_key") or primary.get("api_key_env")):
        raise HTTPException(status_code=400, detail="主通道必须配置 api_key 或 api_key_env")

    cleaned_backups = []
    existing_backups = existing.get("backup", [])
    for index, backup in enumerate(data.get("backup", [])):
        if not isinstance(backup, dict):
            continue
        backup = _merge_channel(
            existing_backups[index] if index < len(existing_backups) and isinstance(existing_backups[index], dict) else {},
            backup,
        )
        if not any((backup.get("name"), backup.get("base_url"), backup.get("base_url_env"), backup.get("model"), backup.get("model_env"))):
            continue
        cleaned_backups.append(backup)
    merged["backup"] = cleaned_backups
    merged["enable_search"] = bool(data.get("enable_search", existing.get("enable_search", True)))
    merged["max_context_messages"] = int(data.get("max_context_messages", existing.get("max_context_messages", 80)) or 80)
    merged["image_context_rounds"] = int(data.get("image_context_rounds", existing.get("image_context_rounds", 5)) or 5)

    _write_json(_api_config_file(), merged)
    return {
        "message": "API 配置更新成功",
        "config": _build_api_config_response(),
    }
