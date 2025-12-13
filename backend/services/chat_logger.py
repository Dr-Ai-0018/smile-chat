"""
ChatLogger - 可观测性日志
记录每轮对话的preset、原始输出、解析结果等
用于调试、复现和行为分析
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ChatLogger:
    """聊天日志记录器"""
    
    def __init__(self, logs_base_path: Optional[Path] = None):
        self.logs_base_path = logs_base_path or (
            Path(__file__).parent.parent.parent / "memory" / "本体"
        )
    
    def _get_logs_dir(self, user_id: int) -> Path:
        """获取用户日志目录"""
        logs_dir = self.logs_base_path / str(user_id) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
    
    def log_request(
        self,
        user_id: int,
        preset: Dict[str, Any],
        condition: str,
        user_message: str,
        context_message_count: int,
    ) -> str:
        """
        记录请求信息
        
        Returns:
            request_id 用于关联响应日志
        """
        request_id = str(uuid.uuid4())[:8]
        
        log_entry = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "preset": preset,
            "condition": condition,
            "user_message_preview": user_message[:200] if user_message else "",
            "context_message_count": context_message_count,
        }
        
        self._write_log(user_id, request_id, log_entry)
        return request_id
    
    def log_response(
        self,
        user_id: int,
        request_id: str,
        raw_content: str,
        parsed_reply: str,
        segments: list,
        did_self_disclosure: bool,
        relationship_stage: str,
        parse_success: bool,
        parse_error: Optional[str] = None,
        latency_ms: Optional[int] = None,
        model: Optional[str] = None,
    ):
        """记录响应信息"""
        log_entry = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "raw_content_preview": raw_content[:500] if raw_content else "",
            "parsed_reply_preview": parsed_reply[:200] if parsed_reply else "",
            "segments_count": len(segments) if segments else 0,
            "did_self_disclosure": did_self_disclosure,
            "relationship_stage": relationship_stage,
            "parse_success": parse_success,
            "parse_error": parse_error,
            "latency_ms": latency_ms,
            "model": model,
        }
        
        self._write_log(user_id, request_id, log_entry, suffix="_response")
    
    def _write_log(
        self,
        user_id: int,
        request_id: str,
        log_entry: Dict[str, Any],
        suffix: str = "",
    ):
        """写入日志文件"""
        logs_dir = self._get_logs_dir(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logs_dir / f"{today}_{request_id}{suffix}.json"
        
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入日志失败: {e}")
    
    def get_recent_logs(self, user_id: int, limit: int = 20) -> list:
        """获取最近的日志"""
        logs_dir = self._get_logs_dir(user_id)
        if not logs_dir.exists():
            return []
        
        log_files = sorted(logs_dir.glob("*.json"), reverse=True)[:limit]
        logs = []
        
        for f in log_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    logs.append(json.load(fp))
            except Exception:
                pass
        
        return logs


# 单例
_chat_logger: Optional[ChatLogger] = None

def get_chat_logger() -> ChatLogger:
    global _chat_logger
    if _chat_logger is None:
        _chat_logger = ChatLogger()
    return _chat_logger
