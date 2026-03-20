"""
AI服务 - 调用多个AI API，支持自动切换
支持图片消息、自动记忆压缩、协议化JSON输出
"""
import asyncio
import base64
import httpx
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)

from storage import JsonStorage
from services.prompt_manager import get_prompt_manager
from services.response_parser import get_response_parser, ParsedResponse
from services.session_state import get_session_state_service, SessionPreset
from services.memory_service import get_memory_service
from services.chat_logger import get_chat_logger

class AIService:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "api_channels.json"
        self.context_config_path = Path(__file__).parent.parent / "config" / "context_config.json"
        self.memory_base_path = Path(__file__).parent.parent.parent / "memory" / "本体"
        self.storage = JsonStorage()
        self.prompt_manager = get_prompt_manager()
        self.response_parser = get_response_parser()
        self.session_state = get_session_state_service()
        self.memory_service = get_memory_service()
        self.chat_logger = get_chat_logger()
        self.config = self._load_config()
        self.context_config = self._load_context_config()

    def refresh_config(self) -> dict:
        """每次请求前重新加载 API 配置，确保管理台修改立即生效。"""
        self.config = self._load_config()
        return self.config

    def refresh_context_config(self) -> dict:
        """每次请求前重新加载上下文配置，确保管理台修改立即生效。"""
        self.context_config = self._load_context_config()
        return self.context_config

    def _summarize_outbound_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary_messages: List[Dict[str, Any]] = []
        for idx, msg in enumerate(messages):
            content = msg.get("content")
            item: Dict[str, Any] = {
                "index": idx,
                "role": msg.get("role"),
            }
            if isinstance(content, str):
                item["text_len"] = len(content)
                item["has_image"] = False
            elif isinstance(content, list):
                text_len = 0
                image_count = 0
                image_mimes: List[str] = []
                image_b64_lens: List[int] = []
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") == "text":
                        text_len += len(str(part.get("text") or ""))
                    elif part.get("type") == "image_url":
                        image_count += 1
                        img_url = ((part.get("image_url") or {}).get("url") or "")
                        if isinstance(img_url, str) and img_url.startswith("data:"):
                            try:
                                header, b64 = img_url.split(",", 1)
                                mime = header[5:].split(";", 1)[0].strip() if header.startswith("data:") else "unknown"
                            except Exception:
                                mime, b64 = "unknown", ""
                            image_mimes.append(mime or "unknown")
                            image_b64_lens.append(len(b64 or ""))
                        else:
                            image_mimes.append("remote_url")
                item["text_len"] = text_len
                item["has_image"] = image_count > 0
                item["image_count"] = image_count
                if image_mimes:
                    item["image_mimes"] = image_mimes
                if image_b64_lens:
                    item["image_b64_lens"] = image_b64_lens
            else:
                item["text_len"] = len(str(content or ""))
                item["has_image"] = False
            summary_messages.append(item)

        return {
            "message_count": len(messages),
            "messages": summary_messages,
        }

    def _build_v2_response_schema(self, for_gemini: bool = False) -> Dict[str, Any]:
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "relationship_stage_judge": {"type": "string", "enum": ["A", "B", "C"]},
                "did_self_disclosure": {"type": "boolean"},
                "reply": {"type": "string"},
                "segments": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["relationship_stage_judge", "did_self_disclosure", "reply", "segments"],
        }
        if for_gemini:
            # Gemini 原生支持 propertyOrdering，可显式约束输出字段顺序
            schema["propertyOrdering"] = [
                "relationship_stage_judge",
                "did_self_disclosure",
                "reply",
                "segments",
            ]
        return schema

    def _build_v2_output_contract_text(self) -> str:
        return (
            "你必须只输出一个 JSON 对象，不要输出任何额外文字，不要 Markdown。\n"
            "字段必须且只能包含：\n"
            "- relationship_stage_judge: string enum A/B/C\n"
            "- did_self_disclosure: boolean\n"
            "- reply: string\n"
            "- segments: array of string\n"
        )

    def _build_repair_user_prompt(self, original_user_text: str, bad_text_or_obj: str, error_msg: str) -> str:
        return (
            "你刚才的输出不符合后端要求，需要你立刻修复并重写。\n"
            "要求：只输出一个 JSON 对象，不要任何额外文字，不要 Markdown。\n"
            "字段必须且只能包含：relationship_stage_judge(只能是A/B/C), did_self_disclosure(布尔), reply(字符串), segments(字符串数组)。\n"
            f"原始用户输入：{original_user_text}\n"
            f"错误原因：{error_msg}\n"
            f"你刚才的输出：{bad_text_or_obj}\n"
            "现在请直接输出修复后的 JSON："
        )

    def _resolve_channel_env(self, channel: dict) -> dict:
        if not isinstance(channel, dict):
            return {}

        def _apply(value_key: str, env_key: str) -> None:
            env_var = channel.get(env_key)
            if isinstance(env_var, str) and env_var.strip():
                v = (os.getenv(env_var.strip()) or "").strip()
                if v:
                    channel[value_key] = v

        _apply("name", "name_env")
        _apply("base_url", "base_url_env")
        _apply("model", "model_env")
        # api_key 已通过 api_key_env/api_key 处理（见 _get_api_key）
        return channel

    def _resolve_config_env_indirection(self, config: dict) -> dict:
        if not isinstance(config, dict):
            config = {}

        primary = config.get("primary")
        if not isinstance(primary, dict):
            primary = {}
            config["primary"] = primary
        self._resolve_channel_env(primary)

        backups = config.get("backup")
        if isinstance(backups, list):
            for b in backups:
                if isinstance(b, dict):
                    self._resolve_channel_env(b)

        return config

    def _apply_env_overrides(self, config: dict) -> dict:
        primary = config.get("primary")
        if not isinstance(primary, dict):
            primary = {}
            config["primary"] = primary

        def _env(name: str) -> str:
            return (os.getenv(name) or "").strip()

        v = _env("AI_PRIMARY_NAME")
        if v:
            primary["name"] = v

        v = _env("AI_PRIMARY_BASE_URL")
        if v:
            primary["base_url"] = v

        v = _env("AI_PRIMARY_MODEL")
        if v:
            primary["model"] = v

        v = _env("AI_PRIMARY_API_KEY_ENV")
        if v:
            primary["api_key_env"] = v

        v = _env("AI_PRIMARY_API_KEY")
        if v:
            primary["api_key"] = v

        v = _env("AI_ENABLE_SEARCH")
        if v.lower() in {"1", "true", "yes"}:
            config["enable_search"] = True
        elif v.lower() in {"0", "false", "no"}:
            config["enable_search"] = False

        v = _env("AI_MAX_CONTEXT_MESSAGES")
        if v.isdigit():
            config["max_context_messages"] = int(v)

        v = _env("AI_IMAGE_CONTEXT_ROUNDS")
        if v.isdigit():
            config["image_context_rounds"] = int(v)

        return config

    def _apply_env_overrides_context(self, config: dict) -> dict:
        def _env(name: str) -> str:
            return (os.getenv(name) or "").strip()

        v = _env("AI_CONTEXT_MAX_MESSAGES")
        if v.isdigit():
            config["max_messages"] = int(v)

        v = _env("AI_CONTEXT_MAX_TOKENS")
        if v.isdigit():
            config["max_tokens"] = int(v)

        v = _env("AI_CONTEXT_IMAGE_ROUNDS")
        if v.isdigit():
            config["image_rounds"] = int(v)

        return config
    
    def _load_config(self) -> dict:
        """加载API配置"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "primary": {
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "OPENAI_API_KEY",
                    "model": "gpt-4o-mini",
                    "price": "$0.002/1K tokens"
                },
                "backup": [],
                "system_prompt": "你是启明，用户的好朋友和伙伴。你温暖、真诚、有同理心。请像朋友一样自然地聊天，不要太正式。",
                "enable_search": True,
                "max_context_messages": 80,
                "image_context_rounds": 5
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            config = self._resolve_config_env_indirection(default_config)
            return self._apply_env_overrides(config)
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if not isinstance(config, dict):
            config = {}
        config = self._resolve_config_env_indirection(config)
        return self._apply_env_overrides(config)
    
    def _load_context_config(self) -> dict:
        """加载上下文配置"""
        default_config = {
            "max_messages": 80,
            "max_tokens": 12000,
            "system_prompt_tokens": 100,
            "reserve_tokens": 1000,
            "image_rounds": 5,
        }
        if not self.context_config_path.exists():
            with open(self.context_config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return self._apply_env_overrides_context(default_config)
        
        with open(self.context_config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        config = dict(default_config)
        if isinstance(raw, dict):
            config.update(raw)
        return self._apply_env_overrides_context(config)
    
    def _get_user_memory_dir(self, user_id: int) -> Path:
        """获取用户记忆目录"""
        user_dir = self.memory_base_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def load_user_memory(self, user_id: int) -> str:
        """加载用户最新记忆（使用MemoryService）"""
        content = self.memory_service.read_ltm_text(user_id)
        if content:
            # 只取最后2000字符，避免过长
            if len(content) > 2000:
                content = "...\n" + content[-2000:]
            return content
        return ""
    
    async def chat_with_context(
        self,
        messages: List[Dict],
        user_id: int,
        cancel_event: Optional[asyncio.Event] = None
    ) -> dict:
        """
        带完整上下文的聊天
        messages格式: [{"role": "user/assistant", "content": "...", "image": "base64或null"}]
        """
        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError("聊天请求已被新的消息中断")

        # 加载用户记忆
        user_memory = self.load_user_memory(user_id)
        
        # 构建系统提示
        system_content = self.config.get("system_prompt", "你是启明，用户的好朋友。")
        if user_memory:
            system_content += f"\n\n【关于这位用户的记忆】\n{user_memory}\n【记忆结束】\n\n请基于以上记忆，像朋友一样自然地回复。"
        
        # 构建OpenAI格式的消息
        api_messages = [{"role": "system", "content": system_content}]
        
        # 获取配置
        max_messages = self.config.get("max_context_messages", 80)
        image_rounds = self.config.get("image_context_rounds", 5)
        
        # 裁剪消息到最近N条
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # 先计算哪些消息在图片保留范围内（从后往前数轮次）
        total_msgs = len(recent_messages)
        round_count_from_end = [0] * total_msgs
        current_round = 0
        for i in range(total_msgs - 1, -1, -1):
            if recent_messages[i].get("role") == "assistant":
                current_round += 1
            round_count_from_end[i] = current_round
        
        # 正向遍历构建消息
        for i, msg in enumerate(recent_messages):
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""
            image = msg.get("image")
            
            # 检查是否应该包含图片（在最近N轮内）
            include_image = image and isinstance(image, str) and round_count_from_end[i] <= image_rounds
            
            if include_image:
                # 有图片 - 使用OpenAI的多模态格式
                content_parts = []
                
                # 先添加文字（如果有），如果没有文字则添加提示
                text_content = content if content else "请看这张图片"
                content_parts.append({
                    "type": "text",
                    "text": text_content
                })
                
                # 添加图片
                if image.startswith("data:"):
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": image}
                    })
                else:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                    })
                
                api_messages.append({
                    "role": role,
                    "content": content_parts
                })
            else:
                # 纯文字消息
                api_messages.append({
                    "role": role,
                    "content": content
                })
        
        # 调用API
        return await self._call_api_with_fallback(api_messages, cancel_event)
    
    async def _call_api_with_fallback(
        self,
        messages: List[Dict],
        cancel_event: Optional[asyncio.Event] = None,
        *,
        force_json: bool = False,
        response_schema: Optional[Dict[str, Any]] = None,
        response_mime_type: Optional[str] = None,
    ) -> dict:
        """调用API，支持自动切换备份"""
        # 尝试主API
        try:
            return await self._call_api(
                self.config["primary"],
                messages,
                cancel_event,
                force_json=force_json,
                response_schema=response_schema,
                response_mime_type=response_mime_type,
            )
        except asyncio.CancelledError:
            # 新消息到来，主动取消当前请求
            raise
        except Exception as e:
            print(f"主API调用失败: {e}")
            
            # 尝试备份API
            for backup in self.config.get("backup", []):
                try:
                    print(f"切换到备份API: {backup['name']}")
                    return await self._call_api(
                        backup,
                        messages,
                        cancel_event,
                        force_json=force_json,
                        response_schema=response_schema,
                        response_mime_type=response_mime_type,
                    )
                except Exception as backup_e:
                    print(f"备份API {backup['name']} 调用失败: {backup_e}")
                    continue
            
            raise Exception("所有AI API均不可用")
    
    def _get_api_key(self, api_config: dict) -> str:
        """从环境变量获取API Key"""
        # 优先使用api_key_env指定的环境变量
        env_var = api_config.get("api_key_env", "")
        if env_var:
            # 如果值本身就是 key（以 sk- 开头），直接使用
            if env_var.startswith("sk-"):
                return env_var
            # 否则当作环境变量名去读取
            key = os.environ.get(env_var, "")
            if key:
                return key
        # 兼容旧配置：直接使用api_key字段
        return api_config.get("api_key", "")
    
    async def _call_api(
        self,
        api_config: dict,
        messages: List[Dict],
        cancel_event: Optional[asyncio.Event] = None,
        *,
        force_json: bool = False,
        response_schema: Optional[Dict[str, Any]] = None,
        response_mime_type: Optional[str] = None,
    ) -> dict:
        """调用单个API"""
        base_url = (api_config.get("base_url") or "").strip()
        if not base_url:
            env_hint = api_config.get("base_url_env") or "AI_PRIMARY_BASE_URL"
            raise ValueError(f"API base_url未配置，请设置环境变量: {env_hint}")

        model = (api_config.get("model") or "").strip()
        if not model:
            env_hint = api_config.get("model_env") or "AI_PRIMARY_MODEL"
            raise ValueError(f"API model未配置，请设置环境变量: {env_hint}")

        api_key = self._get_api_key(api_config)
        if not api_key:
            raise ValueError(f"API Key未配置，请设置环境变量: {api_config.get('api_key_env', 'OPENAI_API_KEY')}")

        def _should_use_gemini() -> bool:
            api_type = (api_config.get("api_type") or "").strip().lower()
            if api_type == "gemini":
                return True
            if api_type in ("openai", "chat_completions"):
                return False

            b = (base_url or "").lower().rstrip("/")
            # 只有明确是 Gemini 原生端点时，才走 generateContent。
            # 很多第三方网关虽然代理 Gemini 模型，但接口仍然是 OpenAI 兼容的 /v1/chat/completions。
            if b.endswith("/v1beta") or "/v1beta/" in b:
                return True
            if "generativelanguage.googleapis.com" in b:
                return True
            if b.endswith("/v1") or "/v1/" in b:
                return False

            m = (model or "").lower()
            if "gemini" in m:
                return True

            n = (api_config.get("name") or "").lower()
            if "gemini" in n:
                return True

            return False

        if force_json and response_schema is None:
            response_schema = self._build_v2_response_schema(for_gemini=_should_use_gemini())

        def _extract_openai_content(result: dict) -> Tuple[str, str]:
            choices = result.get("choices")
            content = ""
            reasoning_content = ""
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("message")
                    if isinstance(msg, dict):
                        c = msg.get("content")
                        if isinstance(c, str):
                            content = c
                        elif c is not None:
                            content = str(c)

                        rc = msg.get("reasoning_content")
                        if isinstance(rc, str):
                            reasoning_content = rc
            return content, reasoning_content

        def _extract_gemini_text(result: dict) -> str:
            try:
                return str(result["candidates"][0]["content"]["parts"][0]["text"])
            except Exception:
                return ""

        def _join_system_messages(msgs: List[Dict]) -> str:
            parts: List[str] = []
            for m in msgs:
                if m.get("role") == "system":
                    c = m.get("content")
                    if isinstance(c, str) and c.strip():
                        parts.append(c.strip())
            return "\n\n".join(parts)

        def _to_plain_text(content: Any) -> str:
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts: List[str] = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        t = p.get("text")
                        if isinstance(t, str) and t:
                            texts.append(t)
                return "\n".join(texts)
            if content is None:
                return ""
            return str(content)

        def _parse_data_url(url: str) -> Tuple[Optional[str], Optional[str]]:
            if not isinstance(url, str) or not url.startswith("data:"):
                return None, None
            try:
                header, b64 = url.split(",", 1)
                mime = header[5:].split(";", 1)[0].strip() if header.startswith("data:") else ""
                if not mime:
                    mime = "application/octet-stream"
                return mime, b64
            except Exception:
                return None, None

        def _to_gemini_parts(content: Any) -> List[Dict[str, Any]]:
            if isinstance(content, str):
                t = content.strip("\n")
                return [{"text": t}] if t else []

            if isinstance(content, list):
                parts: List[Dict[str, Any]] = []
                for p in content:
                    if not isinstance(p, dict):
                        continue
                    if p.get("type") == "text":
                        t = p.get("text")
                        if isinstance(t, str) and t.strip():
                            parts.append({"text": t})
                    elif p.get("type") == "image_url":
                        img_url = (p.get("image_url") or {}).get("url")
                        if isinstance(img_url, str):
                            mime, b64 = _parse_data_url(img_url)
                            if mime and b64:
                                parts.append({"inlineData": {"mimeType": mime, "data": b64}})
                return parts

            if content is None:
                return []

            s = str(content).strip("\n")
            return [{"text": s}] if s else []

        def _summarize_openai_messages_for_log(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            summary: List[Dict[str, Any]] = []
            for idx, msg in enumerate(msgs):
                item: Dict[str, Any] = {
                    "index": idx,
                    "role": msg.get("role"),
                    "content_type": type(msg.get("content")).__name__,
                }
                content = msg.get("content")
                if isinstance(content, str):
                    item["text_len"] = len(content)
                    item["has_image"] = False
                elif isinstance(content, list):
                    text_len = 0
                    image_count = 0
                    image_mimes: List[str] = []
                    image_b64_lens: List[int] = []
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") == "text":
                            text_len += len(str(part.get("text") or ""))
                        elif part.get("type") == "image_url":
                            image_count += 1
                            img_url = ((part.get("image_url") or {}).get("url") or "")
                            if isinstance(img_url, str) and img_url.startswith("data:"):
                                mime, b64 = _parse_data_url(img_url)
                                image_mimes.append(mime or "unknown")
                                image_b64_lens.append(len(b64 or ""))
                            else:
                                image_mimes.append("remote_url")
                    item["text_len"] = text_len
                    item["has_image"] = image_count > 0
                    item["image_count"] = image_count
                    if image_mimes:
                        item["image_mimes"] = image_mimes
                    if image_b64_lens:
                        item["image_b64_lens"] = image_b64_lens
                else:
                    item["text_len"] = len(str(content or ""))
                    item["has_image"] = False
                summary.append(item)
            return summary

        def _summarize_gemini_contents_for_log(contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            summary: List[Dict[str, Any]] = []
            for idx, msg in enumerate(contents):
                parts = msg.get("parts") if isinstance(msg, dict) else []
                text_len = 0
                image_count = 0
                image_mimes: List[str] = []
                image_b64_lens: List[int] = []
                if isinstance(parts, list):
                    for part in parts:
                        if not isinstance(part, dict):
                            continue
                        if "text" in part:
                            text_len += len(str(part.get("text") or ""))
                        inline_data = part.get("inlineData") or {}
                        if isinstance(inline_data, dict) and inline_data:
                            image_count += 1
                            image_mimes.append(str(inline_data.get("mimeType") or "unknown"))
                            image_b64_lens.append(len(str(inline_data.get("data") or "")))
                item: Dict[str, Any] = {
                    "index": idx,
                    "role": msg.get("role") if isinstance(msg, dict) else None,
                    "text_len": text_len,
                    "has_image": image_count > 0,
                    "image_count": image_count,
                }
                if image_mimes:
                    item["image_mimes"] = image_mimes
                if image_b64_lens:
                    item["image_b64_lens"] = image_b64_lens
                summary.append(item)
            return summary

        def _log_outbound_request(transport: str, payload_summary: Dict[str, Any]) -> None:
            log_payload = {
                "transport": transport,
                "base_url": base_url,
                "model": model,
                "force_json": force_json,
                **payload_summary,
            }
            print("[AI DEBUG] outbound_request=" + json.dumps(log_payload, ensure_ascii=False))

        async def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> httpx.Response:
            async with httpx.AsyncClient(timeout=120.0) as client:
                request_coro = client.post(url, headers=headers, json=payload)
                if cancel_event:
                    api_task = asyncio.create_task(request_coro)
                    cancel_task = asyncio.create_task(cancel_event.wait())
                    done, _ = await asyncio.wait(
                        {api_task, cancel_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    if cancel_task in done:
                        api_task.cancel()
                        try:
                            await api_task
                        except asyncio.CancelledError:
                            pass
                        raise asyncio.CancelledError("AI调用在请求被替换后取消")

                    cancel_task.cancel()
                    resp = await api_task
                    await resp.aread()
                    return resp

                resp = await request_coro
                await resp.aread()
                return resp

        async def _call_openai_chat_completions() -> dict:
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            base_payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 2000,
            }

            payloads: List[Dict[str, Any]] = []
            if force_json:
                openai_schema = dict(response_schema or self._build_v2_response_schema())
                openai_schema.pop("propertyOrdering", None)
                payload1 = dict(base_payload)
                payload1["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "smile_chat_response",
                        "schema": openai_schema,
                        "strict": True,
                    },
                }
                payloads.append(payload1)

                payload2 = dict(base_payload)
                payload2["response_format"] = {"type": "json_object"}
                payloads.append(payload2)

            payloads.append(base_payload)

            last_error: Optional[Exception] = None
            for payload in payloads:
                _log_outbound_request(
                    "openai_chat_completions",
                    {
                        "url": url,
                        "message_count": len(payload.get("messages") or []),
                        "messages": _summarize_openai_messages_for_log(payload.get("messages") or []),
                    },
                )
                resp = await _post_json(url, headers, payload)
                upstream_request_id = resp.headers.get("X-Oneapi-Request-Id") or resp.headers.get("X-Request-Id")
                if resp.status_code == 404:
                    raise httpx.HTTPStatusError("openai endpoint not found", request=resp.request, response=resp)

                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if force_json and e.response.status_code in (400, 422):
                        last_error = e
                        continue
                    raise

                result = resp.json()
                content, reasoning_content = _extract_openai_content(result)
                return {
                    "content": content,
                    "reasoning_content": reasoning_content,
                    "upstream_request_id": upstream_request_id,
                }

            if last_error is not None:
                raise last_error
            raise ValueError("OpenAI调用失败")

        async def _call_gemini_generate_content() -> dict:
            base = base_url.rstrip("/")
            if base.endswith("/v1beta"):
                url = f"{base}/models/{model}:generateContent"
            else:
                url = f"{base}/v1beta/models/{model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
                "Authorization": f"Bearer {api_key}",
            }

            system_instruction_parts: List[Dict[str, Any]] = []
            contents: List[Dict[str, Any]] = []
            seen_non_system = False
            for m in messages:
                role = m.get("role")
                if role == "system":
                    parts = _to_gemini_parts(m.get("content"))
                    if not parts:
                        continue
                    if not seen_non_system:
                        # 前置 system 消息仍走 systemInstruction
                        system_instruction_parts.extend(parts)
                    else:
                        # 保留中后段 system 消息在消息序列中的相对位置（例如末尾 preset）
                        forwarded_text = (
                            "【系统附加上下文（仅供内部推理，不可原样复述）】\n"
                            + _to_plain_text(m.get("content"))
                        )
                        forwarded_parts = _to_gemini_parts(forwarded_text)
                        if forwarded_parts:
                            contents.append({"role": "user", "parts": forwarded_parts})
                    continue
                seen_non_system = True
                gemini_role = "model" if role == "assistant" else "user"
                parts = _to_gemini_parts(m.get("content"))
                if parts:
                    contents.append({"role": gemini_role, "parts": parts})

            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                },
            }
            if system_instruction_parts:
                payload["systemInstruction"] = {"parts": system_instruction_parts}

            system_text_len = 0
            for part in system_instruction_parts:
                if isinstance(part, dict):
                    system_text_len += len(str(part.get("text") or ""))

            if force_json:
                payload["generationConfig"]["responseMimeType"] = response_mime_type or "application/json"
                gemini_schema = dict(response_schema or self._build_v2_response_schema(for_gemini=True))
                if "propertyOrdering" not in gemini_schema:
                    gemini_schema["propertyOrdering"] = [
                        "relationship_stage_judge",
                        "did_self_disclosure",
                        "reply",
                        "segments",
                    ]
                payload["generationConfig"]["responseSchema"] = gemini_schema

            _log_outbound_request(
                "gemini_generate_content",
                {
                    "url": url,
                    "system_text_len": system_text_len,
                    "message_count": len(contents),
                    "messages": _summarize_gemini_contents_for_log(contents),
                },
            )
            resp = await _post_json(url, headers, payload)
            upstream_request_id = resp.headers.get("X-Oneapi-Request-Id") or resp.headers.get("X-Request-Id")
            resp.raise_for_status()
            result = resp.json()
            content = _extract_gemini_text(result)
            return {
                "content": content,
                "reasoning_content": "",
                "upstream_request_id": upstream_request_id,
            }
        
        prefer_gemini = _should_use_gemini()

        if prefer_gemini:
            try:
                return await _call_gemini_generate_content()
            except httpx.HTTPStatusError as e:
                if e.response is not None and e.response.status_code == 404:
                    return await _call_openai_chat_completions()
                body = ""
                try:
                    body = (e.response.text or "").strip() if e.response is not None else ""
                except Exception:
                    body = ""
                if len(body) > 2000:
                    body = body[:2000] + "..."
                raise ValueError(
                    f"上游API错误 {e.response.status_code if e.response is not None else 'unknown'} ({e.response.reason_phrase if e.response is not None else 'unknown'}): {body}"
                ) from e

        try:
            return await _call_openai_chat_completions()
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 404:
                return await _call_gemini_generate_content()
            body = ""
            try:
                body = (e.response.text or "").strip() if e.response is not None else ""
            except Exception:
                body = ""
            if len(body) > 2000:
                body = body[:2000] + "..."
            raise ValueError(
                f"上游API错误 {e.response.status_code if e.response is not None else 'unknown'} ({e.response.reason_phrase if e.response is not None else 'unknown'}): {body}"
            ) from e

    async def recognize_image(self, image_path: str, user_id: int) -> str:
        """识别图片内容"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(image_path)

        ext = path.suffix.lower().lstrip(".")
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "bmp": "image/bmp",
        }
        mime = mime_map.get(ext, "image/jpeg")
        image_b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        data_url = f"data:{mime};base64,{image_b64}"

        messages_for_api = [
            {"role": "system", "content": "你是一个擅长描述图片内容的助手。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请用简洁中文描述这张图片的主要内容，并指出可能的细节。"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        result = await self._call_api_with_fallback(messages_for_api)
        return result.get("content", "")

    async def compress_memory(self, user_id: int, limit: int = 120) -> str:
        """手动触发压缩记忆"""
        self.refresh_config()
        history_items = self.storage.get_chat_history(user_id=user_id, limit=limit)
        messages = []
        for item in history_items:
            messages.append(
                {
                    "role": item.get("role"),
                    "content": item.get("content", "") or "",
                    "image": item.get("image"),
                }
            )
        return await self.compress_and_merge_memory(user_id, messages)
    
    async def compress_and_merge_memory(self, user_id: int, messages: List[Dict]) -> str:
        """
        压缩消息并融合到已有记忆（使用MemoryService结构化存储）
        这是自动调用的，用于动态记忆管理
        """
        if not messages:
            return ""

        self.refresh_config()
        
        # 使用MemoryService读取现有记忆
        existing_memory = self.memory_service.read_ltm_text(user_id)
        
        # 格式化新对话
        new_conversation = []
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "启明"
            content = msg.get("content", "")
            if msg.get("image"):
                content = "[发送了图片] " + content
            new_conversation.append(f"{role}: {content}")
        
        new_conv_text = "\n".join(new_conversation)
        
        # 构建压缩提示
        compress_prompt = f"""你是记忆管理助手。请分析以下新对话，提取关键信息并融合到已有记忆中。

【已有记忆】
{existing_memory if existing_memory else "（暂无记忆）"}

【新对话】
{new_conv_text}

请输出更新后的完整记忆，要求：
1. 保留重要的用户信息（姓名、偏好、习惯等）
2. 更新或补充新了解到的信息
3. 删除过时或不重要的细节
4. 保持简洁，总字数控制在800字以内
5. 直接输出记忆内容，不要有多余的开头语

输出格式示例：
【用户信息】
- 姓名：xxx
- 职业：xxx

【偏好习惯】
- xxx

【重要事项】
- xxx
"""
        
        try:
            messages_for_api = [
                {"role": "system", "content": "你是记忆管理助手，负责整理和压缩对话记忆。"},
                {"role": "user", "content": compress_prompt}
            ]
            
            result = await self._call_api_with_fallback(messages_for_api)
            compressed_memory = result["content"]
            
            # 使用MemoryService保存结构化LTM（自动版本管理）
            source_window = {
                "message_count": len(messages),
                "compress_time": get_china_now().isoformat(),
            }
            self.memory_service.write_ltm(user_id, compressed_memory, source_window)
            
            print(f"用户 {user_id} 的记忆已自动压缩更新")
            return compressed_memory
            
        except Exception as e:
            print(f"自动压缩记忆失败: {e}")
            return ""
    
    # 保留旧方法兼容
    async def chat(self, messages: List[Dict], user_id: int) -> dict:
        """旧版聊天接口（兼容）"""
        return await self.chat_with_context(messages, user_id)
    
    # ========== 协议化输出 v2 ==========
    
    async def chat_with_context_v2(
        self,
        messages: List[Dict],
        user_id: int,
        cancel_event: Optional[asyncio.Event] = None
    ) -> Dict[str, Any]:
        """
        协议化聊天接口 v2
        
        按照reference文档的Context组装规范：
        1. System 固定规则块（根据condition加载提示词）
        2. LTM 长时记忆摘要
        3. Recent + Current 近期对话与当前用户消息
        4. State 动态状态块（preset JSON）
        
        Returns:
            {
                "reply": str,           # 完整回复
                "segments": List[str],  # 分句数组
                "content": str,         # 兼容旧接口
                "meta": {
                    "did_self_disclosure": bool,
                    "relationship_stage": str,
                    "condition": str,
                    "parse_success": bool
                }
            }
        """
        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError("聊天请求已被新的消息中断")

        self.refresh_config()
        self.refresh_context_config()
        
        # 1. 获取实验条件和加载对应提示词
        condition = self.session_state.get_condition(user_id)
        system_prompt = self.prompt_manager.get_system_prompt(condition)
        
        # 2. 计算动态状态参数 (preset)
        preset = self.session_state.compute_preset(user_id)
        
        # 3. 加载长期记忆
        ltm_summary = self.load_user_memory(user_id)
        
        # 4. 构建API消息
        api_messages = self._build_context_messages_v2(
            system_prompt=system_prompt,
            preset=preset,
            ltm_summary=ltm_summary,
            messages=messages,
        )
        
        # 获取用户最后一条消息用于日志
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break
        
        # 记录请求日志
        exp_state = self.storage.get_user_experiment_state(user_id)
        context_summary = {
            "input_message_count": len(messages),
            "api_message_count": len(api_messages),
            "user_message_count": sum(1 for m in messages if m.get("role") == "user"),
            "assistant_message_count": sum(1 for m in messages if m.get("role") == "assistant"),
            "image_message_count": sum(1 for m in messages if m.get("image")),
            "ltm_length": len(ltm_summary or ""),
            "system_prompt_length": len(system_prompt or ""),
        }
        outbound_summary = self._summarize_outbound_messages(api_messages)

        request_id = self.chat_logger.log_request(
            user_id=user_id,
            preset=preset.to_dict(),
            condition=condition,
            user_message=user_msg,
            context_message_count=len(api_messages),
            state_snapshot={
                "current_round_count": exp_state.get("current_round_count", 0),
                "weekly_checkin_count": exp_state.get("weekly_checkin_count", 0),
                "weekly_survey_popup_shown": exp_state.get("weekly_survey_popup_shown", False),
                "current_week_key": exp_state.get("current_week_key"),
                "session_start_time": exp_state.get("session_start_time"),
                "last_user_message_time": exp_state.get("last_user_message_time"),
                "last_session_end_time": exp_state.get("last_session_end_time"),
            },
            context_summary=context_summary,
            outbound_summary=outbound_summary,
            model=self.config.get("primary", {}).get("model"),
        )
        
        import time
        start_time = time.time()

        schema = self._build_v2_response_schema()
        raw_result: Dict[str, Any] = {}
        raw_content = ""
        parsed: ParsedResponse = self.response_parser.parse("", last_relationship_stage=preset.last_relationship_stage)
        attempts = 0

        max_attempts = 3
        try:
            while attempts < max_attempts:
                attempts += 1
                raw_result = await self._call_api_with_fallback(
                    api_messages,
                    cancel_event,
                    force_json=True,
                    response_schema=schema,
                    response_mime_type="application/json",
                )
                raw_content = raw_result.get("content", "") or ""

                parsed = self.response_parser.parse(
                    raw_content,
                    last_relationship_stage=preset.last_relationship_stage,
                )
                if parsed.parse_success:
                    break

                if cancel_event and cancel_event.is_set():
                    raise asyncio.CancelledError("聊天请求已被新的消息中断")

                if attempts < max_attempts:
                    repair_prompt = self._build_repair_user_prompt(
                        original_user_text=user_msg,
                        bad_text_or_obj=(raw_content[:2000] if raw_content else ""),
                        error_msg=(parsed.parse_error or "schema validation failed"),
                    )
                    api_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "system", "content": self._build_v2_output_contract_text()},
                        {"role": "system", "content": f"【当前状态参数】\n{preset.to_json()}"},
                    ]
                    if ltm_summary:
                        api_messages.append({"role": "system", "content": f"【关于这位用户的记忆】\n{ltm_summary}"})
                    api_messages.append({"role": "user", "content": repair_prompt})
        except BaseException as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            self.chat_logger.log_response(
                user_id=user_id,
                request_id=request_id,
                raw_content=raw_content,
                parsed_reply=parsed.reply,
                segments=parsed.segments,
                did_self_disclosure=parsed.did_self_disclosure,
                relationship_stage=parsed.relationship_stage_judge,
                parse_success=False,
                parse_error=str(exc),
                latency_ms=latency_ms,
                model=self.config.get("primary", {}).get("model"),
                reasoning_content=raw_result.get("reasoning_content", "") or "",
                upstream_request_id=raw_result.get("upstream_request_id"),
                attempts=attempts,
                response_meta={
                    "condition": condition,
                    "did_self_disclosure": parsed.did_self_disclosure,
                    "relationship_stage_judge": parsed.relationship_stage_judge,
                    "failure_type": exc.__class__.__name__,
                },
            )
            raise

        latency_ms = int((time.time() - start_time) * 1000)

        # 记录响应日志
        self.chat_logger.log_response(
            user_id=user_id,
            request_id=request_id,
            raw_content=raw_content,
            parsed_reply=parsed.reply,
            segments=parsed.segments,
            did_self_disclosure=parsed.did_self_disclosure,
            relationship_stage=parsed.relationship_stage_judge,
            parse_success=parsed.parse_success,
            parse_error=parsed.parse_error,
            latency_ms=latency_ms,
            model=self.config.get("primary", {}).get("model"),
            reasoning_content=raw_result.get("reasoning_content", "") or "",
            upstream_request_id=raw_result.get("upstream_request_id"),
            attempts=attempts,
            response_meta={
                "condition": condition,
                "did_self_disclosure": parsed.did_self_disclosure,
                "relationship_stage_judge": parsed.relationship_stage_judge,
            },
        )
        
        # 7. 更新会话状态
        self.session_state.update_after_response(
            user_id=user_id,
            relationship_stage=parsed.relationship_stage_judge,
            did_self_disclosure=parsed.did_self_disclosure
        )
        
        # 8. 构建返回结果
        return {
            "reply": parsed.reply,
            "segments": parsed.segments,
            "content": parsed.reply,  # 兼容旧接口
            "meta": {
                "did_self_disclosure": parsed.did_self_disclosure,
                "relationship_stage": parsed.relationship_stage_judge,
                "relationship_stage_judge": parsed.relationship_stage_judge,
                "condition": condition,
                "parse_success": parsed.parse_success,
                "parse_error": parsed.parse_error,
                "request_id": request_id,
                "latency_ms": latency_ms,
                "upstream_request_id": raw_result.get("upstream_request_id"),
                "attempts": attempts,
            }
        }
    
    def _build_context_messages_v2(
        self,
        system_prompt: str,
        preset: SessionPreset,
        ltm_summary: str,
        messages: List[Dict],
    ) -> List[Dict]:
        """
        按固定顺序构建Context消息
        
        顺序: System → LTM → Recent/Current → State(preset)
        """
        api_messages = []
        
        # 1. System 固定规则块
        api_messages.append({
            "role": "system",
            "content": system_prompt
        })

        api_messages.append({
            "role": "system",
            "content": self._build_v2_output_contract_text()
        })

        # 2. LTM 长时记忆摘要
        if ltm_summary:
            api_messages.append({
                "role": "system",
                "content": f"【关于这位用户的记忆】\n{ltm_summary}"
            })
        
        # 3. Recent 近期对话 + Current 用户消息
        max_messages = self.context_config.get("max_messages", 80)
        image_rounds = self.context_config.get("image_rounds", 5)
        
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # 计算图片保留范围
        total_msgs = len(recent_messages)
        round_count_from_end = [0] * total_msgs
        current_round = 0
        for i in range(total_msgs - 1, -1, -1):
            if recent_messages[i].get("role") == "assistant":
                current_round += 1
            round_count_from_end[i] = current_round
        
        # 构建消息
        for i, msg in enumerate(recent_messages):
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""
            image = msg.get("image")
            
            include_image = image and isinstance(image, str) and round_count_from_end[i] <= image_rounds
            
            if include_image:
                content_parts = []
                # 如果没有文字内容，添加提示文本让模型知道要看图片
                text_content = content if content else "请看这张图片"
                content_parts.append({"type": "text", "text": text_content})
                
                if image.startswith("data:"):
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": image}
                    })
                else:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                    })
                
                api_messages.append({"role": role, "content": content_parts})
            else:
                api_messages.append({"role": role, "content": content})

        # 4. State 动态状态块 (preset JSON)
        state_json = preset.to_json()
        api_messages.append({
            "role": "system",
            "content": f"【当前状态参数】\n{state_json}"
        })
        
        return api_messages
