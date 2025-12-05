"""
AI服务 - 调用多个AI API，支持自动切换
支持图片消息、自动记忆压缩
"""
import httpx
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class AIService:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "api_channels.json"
        self.context_config_path = Path(__file__).parent.parent / "config" / "context_config.json"
        self.memory_base_path = Path(__file__).parent.parent.parent / "memory" / "本体"
        self.config = self._load_config()
        self.context_config = self._load_context_config()
    
    def _load_config(self) -> dict:
        """加载API配置"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "primary": {
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "your-api-key",
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
            
            return default_config
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
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
            return default_config
        
        with open(self.context_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _get_user_memory_dir(self, user_id: int) -> Path:
        """获取用户记忆目录"""
        user_dir = self.memory_base_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def load_user_memory(self, user_id: int) -> str:
        """加载用户最新记忆"""
        memory_dir = self._get_user_memory_dir(user_id)
        
        # 读取长期记忆
        long_term_file = memory_dir / "memory" / "long_term.txt"
        if long_term_file.exists():
            content = long_term_file.read_text(encoding="utf-8").strip()
            if content:
                # 只取最后2000字符，避免过长
                if len(content) > 2000:
                    content = "...\n" + content[-2000:]
                return content
        
        return ""
    
    async def chat_with_context(self, messages: List[Dict], user_id: int) -> dict:
        """
        带完整上下文的聊天
        messages格式: [{"role": "user/assistant", "content": "...", "image": "base64或null"}]
        """
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
        return await self._call_api_with_fallback(api_messages)
    
    async def _call_api_with_fallback(self, messages: List[Dict]) -> dict:
        """调用API，支持自动切换备份"""
        # 尝试主API
        try:
            return await self._call_api(self.config["primary"], messages)
        except Exception as e:
            print(f"主API调用失败: {e}")
            
            # 尝试备份API
            for backup in self.config.get("backup", []):
                try:
                    print(f"切换到备份API: {backup['name']}")
                    return await self._call_api(backup, messages)
                except Exception as backup_e:
                    print(f"备份API {backup['name']} 调用失败: {backup_e}")
                    continue
            
            raise Exception("所有AI API均不可用")
    
    async def _call_api(self, api_config: dict, messages: List[Dict]) -> dict:
        """调用单个API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{api_config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": api_config["model"],
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 2000
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            return {"content": content}
    
    async def compress_and_merge_memory(self, user_id: int, messages: List[Dict]):
        """
        压缩消息并融合到已有记忆
        这是自动调用的，用于动态记忆管理
        """
        if not messages:
            return
        
        memory_dir = self._get_user_memory_dir(user_id)
        memory_subdir = memory_dir / "memory"
        memory_subdir.mkdir(parents=True, exist_ok=True)
        long_term_file = memory_subdir / "long_term.txt"
        
        # 读取现有记忆
        existing_memory = ""
        if long_term_file.exists():
            existing_memory = long_term_file.read_text(encoding="utf-8").strip()
        
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
            
            # 保存更新后的记忆
            long_term_file.write_text(compressed_memory, encoding="utf-8")
            
            print(f"用户 {user_id} 的记忆已自动压缩更新")
            
        except Exception as e:
            print(f"自动压缩记忆失败: {e}")
    
    # 保留旧方法兼容
    async def chat(self, messages: List[Dict], user_id: int) -> dict:
        """旧版聊天接口（兼容）"""
        return await self.chat_with_context(messages, user_id)
