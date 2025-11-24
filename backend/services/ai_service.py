"""
AI服务 - 调用多个AI API，支持自动切换
"""
import httpx
import json
from pathlib import Path
from typing import List, Dict, Optional

class AIService:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "api_channels.json"
        self.context_config_path = Path(__file__).parent.parent / "config" / "context_config.json"
        self.config = self._load_config()
        self.context_config = self._load_context_config()
    
    def _load_config(self) -> dict:
        """加载API配置"""
        if not self.config_path.exists():
            # 创建默认配置
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "primary": {
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "your-api-key",
                    "model": "gpt-3.5-turbo",
                    "price": "$0.002/1K tokens"
                },
                "backup": [
                    {
                        "name": "Azure OpenAI",
                        "base_url": "https://your-resource.openai.azure.com",
                        "api_key": "your-api-key",
                        "model": "gpt-35-turbo",
                        "price": "$0.002/1K tokens"
                    }
                ],
                "system_prompt": "你是启明，一个友好的AI助手。请用简洁、温暖的语气回复用户。",
                "enable_search": True
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
                "max_messages": 20,
                "max_tokens": 4000,
                "system_prompt_tokens": 100,
                "reserve_tokens": 1000
            }
            with open(self.context_config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
        
        with open(self.context_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数（简单估算：中文1字约1.5token，英文1词约1token）"""
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)
    
    def _trim_context(self, messages: List[Dict]) -> List[Dict]:
        """裁剪上下文，确保不超过配置的限制"""
        max_messages = self.context_config.get("max_messages", 20)
        max_tokens = self.context_config.get("max_tokens", 4000)
        system_tokens = self.context_config.get("system_prompt_tokens", 100)
        reserve_tokens = self.context_config.get("reserve_tokens", 1000)
        
        # 可用于历史消息的token数
        available_tokens = max_tokens - system_tokens - reserve_tokens
        
        # 从最新消息开始计算
        trimmed_messages = []
        total_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = self._estimate_tokens(msg.get("content", ""))
            
            # 检查是否超过限制
            if len(trimmed_messages) >= max_messages or (total_tokens + msg_tokens) > available_tokens:
                break
            
            trimmed_messages.insert(0, msg)
            total_tokens += msg_tokens
        
        return trimmed_messages
    
    async def chat(self, messages: List[Dict], user_id: int) -> dict:
        """聊天接口 - 支持自动切换API"""
        # 裁剪上下文
        trimmed_messages = self._trim_context(messages)
        
        # 添加系统提示
        full_messages = [
            {"role": "system", "content": self.config["system_prompt"]}
        ] + trimmed_messages
        
        # 尝试主API
        try:
            return await self._call_api(self.config["primary"], full_messages)
        except Exception as e:
            print(f"主API调用失败: {e}")
            
            # 尝试备份API
            for backup in self.config.get("backup", []):
                try:
                    print(f"切换到备份API: {backup['name']}")
                    return await self._call_api(backup, full_messages)
                except Exception as backup_e:
                    print(f"备份API {backup['name']} 调用失败: {backup_e}")
                    continue
            
            # 所有API都失败，返回错误
            raise Exception("所有AI API均不可用")
    
    async def _call_api(self, api_config: dict, messages: List[Dict]) -> dict:
        """调用单个API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": api_config["model"],
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # 尝试解析句子分割
            sentences = self._split_sentences(content)
            
            return {
                "content": content,
                "sentences": sentences
            }
    
    def _split_sentences(self, text: str) -> List[str]:
        """简单的句子分割"""
        # 按照中文和英文标点符号分割
        separators = ["。", "！", "？", ".", "!", "?", "\n"]
        
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in separators:
                if current.strip():
                    sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return sentences
    
    async def recognize_image(self, image_path: str) -> str:
        """图片识别"""
        # TODO: 实现真实的图片识别功能
        # 需要使用支持视觉的模型（如GPT-4V）
        return "图片识别功能开发中"
