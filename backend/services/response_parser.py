"""
ResponseParser - 解析模型JSON输出
支持降级策略，确保parse失败不会500
"""
import json
import re
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ParsedResponse:
    """解析后的模型响应"""
    reply: str
    segments: List[str]
    did_self_disclosure: bool
    relationship_stage_judge: str
    raw_content: str
    parse_success: bool
    parse_error: Optional[str] = None


class ResponseParser:
    """模型响应解析器"""
    
    VALID_STAGES = {"A", "B", "C"}
    REQUIRED_KEYS = {"reply", "segments", "did_self_disclosure", "relationship_stage_judge"}
    
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
        
        json_obj = self._extract_json(content)
        if json_obj is None:
            return self._fallback(content, last_relationship_stage, "JSON parse failed")

        if not isinstance(json_obj, dict):
            return self._fallback(content, last_relationship_stage, f"JSON is not an object: {type(json_obj)}")

        ok, normalized, err = self._validate_schema(json_obj, last_relationship_stage)
        if not ok or normalized is None:
            reply_guess = self._get_string(json_obj, "reply", "")
            segments_guess = self._get_segments(json_obj, reply_guess)
            did_guess = self._get_bool(json_obj, "did_self_disclosure", False)
            stage_guess = self._get_stage(json_obj, last_relationship_stage)

            reply_final = reply_guess.strip() if isinstance(reply_guess, str) else ""
            if not reply_final:
                reply_final = content.strip()

            segments_final = segments_guess if segments_guess else ([reply_final] if reply_final else [])

            return ParsedResponse(
                reply=reply_final,
                segments=segments_final,
                did_self_disclosure=did_guess,
                relationship_stage_judge=stage_guess,
                raw_content=content,
                parse_success=False,
                parse_error=err or "schema validation failed",
            )

        return ParsedResponse(
            reply=normalized["reply"],
            segments=normalized["segments"],
            did_self_disclosure=normalized["did_self_disclosure"],
            relationship_stage_judge=normalized["relationship_stage_judge"],
            raw_content=content,
            parse_success=True,
        )

    def _validate_schema(
        self,
        obj: Dict[str, Any],
        last_relationship_stage: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        keys = set(obj.keys())
        if keys != self.REQUIRED_KEYS:
            missing = sorted(self.REQUIRED_KEYS - keys)
            extra = sorted(keys - self.REQUIRED_KEYS)
            return False, None, f"schema keys mismatch. missing={missing}, extra={extra}"

        reply = obj.get("reply")
        if not isinstance(reply, str):
            return False, None, "reply must be string"

        segments = obj.get("segments")
        if not (isinstance(segments, list) and all(isinstance(x, str) for x in segments)):
            return False, None, "segments must be list[str]"

        did_self_disclosure = obj.get("did_self_disclosure")
        if not isinstance(did_self_disclosure, bool):
            return False, None, "did_self_disclosure must be bool"

        relationship_stage = obj.get("relationship_stage_judge")
        if not (isinstance(relationship_stage, str) and relationship_stage.upper() in self.VALID_STAGES):
            return False, None, "relationship_stage_judge must be one of A/B/C"

        normalized_segments = [s for s in segments if isinstance(s, str) and s.strip()]
        if not normalized_segments and reply.strip():
            normalized_segments = [reply.strip()]

        normalized = {
            "reply": reply.strip(),
            "segments": normalized_segments,
            "did_self_disclosure": did_self_disclosure,
            "relationship_stage_judge": relationship_stage.upper(),
        }
        if not normalized["relationship_stage_judge"]:
            normalized["relationship_stage_judge"] = last_relationship_stage

        return True, normalized, None
    
    def _extract_json(self, content: str) -> Optional[Any]:
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
    
    def _get_segments(self, obj: dict, fallback_reply: str) -> List[str]:
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

        segments: List[str] = []
        if reply:
            # 先按空行分段（markdown 段落）
            blocks = [b.strip() for b in re.split(r"\n\s*\n+", reply) if b and b.strip()]
            for b in blocks:
                # 再按中文句末标点拆分，尽量保留 ? ! 等语气
                parts = re.split(r"(?<=[。！？!?])\s*", b)
                for p in parts:
                    p = p.strip()
                    if p:
                        segments.append(p)

        return ParsedResponse(
            reply=reply,
            segments=segments if segments else ([reply] if reply else []),
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
