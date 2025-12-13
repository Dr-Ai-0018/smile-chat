"""
ResponseParser - 解析模型JSON输出
支持降级策略，确保parse失败不会500
"""
import json
import re
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ParsedResponse:
    """解析后的模型响应"""
    reply: str
    segments: list[str]
    did_self_disclosure: bool
    relationship_stage_judge: str
    raw_content: str
    parse_success: bool
    parse_error: Optional[str] = None


class ResponseParser:
    """模型响应解析器"""
    
    VALID_STAGES = {"A", "B", "C"}
    
    def parse(self, content: str, last_relationship_stage: str = "A") -> ParsedResponse:
        """
        解析模型输出的JSON
        
        Args:
            content: 模型原始输出
            last_relationship_stage: 上一轮的关系阶段（降级时使用）
        
        Returns:
            ParsedResponse 对象
        """
        if not content:
            return self._fallback("", last_relationship_stage, "empty content")
        
        # 尝试提取JSON
        json_obj = self._extract_json(content)
        
        if json_obj is None:
            return self._fallback(content, last_relationship_stage, "JSON parse failed")
        
        # 提取字段
        reply = self._get_string(json_obj, "reply", content)
        segments = self._get_segments(json_obj, reply)
        did_self_disclosure = self._get_bool(json_obj, "did_self_disclosure", False)
        relationship_stage = self._get_stage(json_obj, last_relationship_stage)
        
        return ParsedResponse(
            reply=reply,
            segments=segments,
            did_self_disclosure=did_self_disclosure,
            relationship_stage_judge=relationship_stage,
            raw_content=content,
            parse_success=True,
        )
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """尝试从内容中提取JSON对象"""
        content = content.strip()
        
        # 直接尝试解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 {...} 部分
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # 尝试移除markdown代码块
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _get_string(self, obj: dict, key: str, default: str) -> str:
        """安全获取字符串字段"""
        val = obj.get(key)
        if isinstance(val, str):
            return val
        return default
    
    def _get_segments(self, obj: dict, fallback_reply: str) -> list[str]:
        """获取segments数组"""
        segments = obj.get("segments")
        if isinstance(segments, list) and len(segments) > 0:
            return [str(s) for s in segments if s]
        # 降级：把reply当作单条
        return [fallback_reply] if fallback_reply else []
    
    def _get_bool(self, obj: dict, key: str, default: bool) -> bool:
        """安全获取布尔字段"""
        val = obj.get(key)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return default
    
    def _get_stage(self, obj: dict, default: str) -> str:
        """获取关系阶段"""
        stage = obj.get("relationship_stage_judge")
        if isinstance(stage, str) and stage.upper() in self.VALID_STAGES:
            return stage.upper()
        return default
    
    def _fallback(self, content: str, last_stage: str, error: str) -> ParsedResponse:
        """降级策略"""
        reply = content.strip() if content else ""
        return ParsedResponse(
            reply=reply,
            segments=[reply] if reply else [],
            did_self_disclosure=False,
            relationship_stage_judge=last_stage,
            raw_content=content,
            parse_success=False,
            parse_error=error,
        )


# 单例
_parser: Optional[ResponseParser] = None

def get_response_parser() -> ResponseParser:
    global _parser
    if _parser is None:
        _parser = ResponseParser()
    return _parser
