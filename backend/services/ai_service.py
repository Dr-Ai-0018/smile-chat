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
from typing import List, Dict, Optional, Any
from datetime import datetime

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
        if not self.context_config_path.exists():
            default_config = {
                "max_messages": 80,
                "max_tokens": 12000,
                "image_rounds": 5
            }
            with open(self.context_config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return self._apply_env_overrides_context(default_config)
        
        with open(self.context_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if not isinstance(config, dict):
            config = {}
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
                
                # 先添加文字（如果有）
                if content:
                    content_parts.append({
                        "type": "text",
                        "text": content
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
        cancel_event: Optional[asyncio.Event] = None
    ) -> dict:
        """调用API，支持自动切换备份"""
        # 尝试主API
        try:
            return await self._call_api(self.config["primary"], messages, cancel_event)
        except asyncio.CancelledError:
            # 新消息到来，主动取消当前请求
            raise
        except Exception as e:
            print(f"主API调用失败: {e}")
            
            # 尝试备份API
            for backup in self.config.get("backup", []):
                try:
                    print(f"切换到备份API: {backup['name']}")
                    return await self._call_api(backup, messages, cancel_event)
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
        cancel_event: Optional[asyncio.Event] = None
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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            request_coro = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 2000
                }
            )

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
                response = await api_task
            else:
                response = await request_coro
            
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                body = ""
                try:
                    body = (e.response.text or "").strip()
                except Exception:
                    body = ""
                if len(body) > 2000:
                    body = body[:2000] + "..."
                raise ValueError(
                    f"上游API错误 {e.response.status_code} ({e.response.reason_phrase}): {body}"
                ) from e

            result = response.json()

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

            return {"content": content, "reasoning_content": reasoning_content}

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
            
            result = await self._call_api(self.config["primary"], messages_for_api)
            compressed_memory = result["content"]
            
            # 使用MemoryService保存结构化LTM（自动版本管理）
            source_window = {
                "message_count": len(messages),
                "compress_time": datetime.now().isoformat(),
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
        2. State 动态状态块（preset JSON）
        3. LTM 长时记忆摘要
        4. Recent 近期对话
        5. Current 用户消息
        
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
        request_id = self.chat_logger.log_request(
            user_id=user_id,
            preset=preset.to_dict(),
            condition=condition,
            user_message=user_msg,
            context_message_count=len(api_messages),
        )
        
        import time
        start_time = time.time()
        
        # 5. 调用API
        raw_result = await self._call_api_with_fallback(api_messages, cancel_event)
        raw_content = raw_result.get("content", "")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 6. 解析JSON响应
        parsed = self.response_parser.parse(
            raw_content,
            last_relationship_stage=preset.last_relationship_stage
        )
        
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
                "condition": condition,
                "parse_success": parsed.parse_success,
                "parse_error": parsed.parse_error,
                "request_id": request_id,
                "latency_ms": latency_ms,
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
        
        顺序: System → State(preset) → LTM → Recent → Current
        """
        api_messages = []
        
        # 1. System 固定规则块
        api_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 2. State 动态状态块 (preset JSON)
        state_json = preset.to_json()
        api_messages.append({
            "role": "system",
            "content": f"【当前状态参数】\n{state_json}"
        })
        
        # 3. LTM 长时记忆摘要
        if ltm_summary:
            api_messages.append({
                "role": "system",
                "content": f"【关于这位用户的记忆】\n{ltm_summary}"
            })
        
        # 4. Recent 近期对话 + Current 用户消息
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
                if content:
                    content_parts.append({"type": "text", "text": content})
                
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
        
        return api_messages
