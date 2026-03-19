"""
ChatLogger - 可观测性日志
记录每轮对话的请求、响应、上下文摘要与关键状态快照。
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))


def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)


def _parse_iso(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=CHINA_TZ)
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHINA_TZ)
        return dt
    except Exception:
        return datetime.min.replace(tzinfo=CHINA_TZ)


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
        *,
        state_snapshot: Optional[Dict[str, Any]] = None,
        context_summary: Optional[Dict[str, Any]] = None,
        outbound_summary: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
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
            "timestamp": get_china_now().isoformat(),
            "type": "request",
            "preset": preset,
            "condition": condition,
            "user_message_preview": user_message[:500] if user_message else "",
            "context_message_count": context_message_count,
            "state_snapshot": state_snapshot or {},
            "context_summary": context_summary or {},
            "outbound_summary": outbound_summary or {},
            "model": model,
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
        reasoning_content: str = "",
        upstream_request_id: Optional[str] = None,
        attempts: Optional[int] = None,
        response_meta: Optional[Dict[str, Any]] = None,
    ):
        """记录响应信息"""
        log_entry = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": get_china_now().isoformat(),
            "type": "response",
            "raw_content_preview": raw_content[:1200] if raw_content else "",
            "reasoning_content_preview": reasoning_content[:1200] if reasoning_content else "",
            "parsed_reply_preview": parsed_reply[:500] if parsed_reply else "",
            "segments_count": len(segments) if segments else 0,
            "segments_preview": [str(s)[:200] for s in (segments or [])[:5]],
            "did_self_disclosure": did_self_disclosure,
            "relationship_stage": relationship_stage,
            "parse_success": parse_success,
            "parse_error": parse_error,
            "latency_ms": latency_ms,
            "model": model,
            "upstream_request_id": upstream_request_id,
            "attempts": attempts,
            "response_meta": response_meta or {},
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
        today = get_china_now().strftime("%Y-%m-%d")
        log_file = logs_dir / f"{today}_{request_id}{suffix}.json"

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入日志失败: {e}")

    def _load_log_file(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return None

    def get_recent_logs(self, user_id: int, limit: int = 20) -> list:
        """获取最近的原始日志文件内容"""
        logs_dir = self._get_logs_dir(user_id)
        if not logs_dir.exists():
            return []

        log_files = sorted(logs_dir.glob("*.json"), reverse=True)[:limit]
        logs: List[Dict[str, Any]] = []

        for f in log_files:
            data = self._load_log_file(f)
            if data:
                logs.append(data)

        return logs

    def get_paired_logs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """按 request_id 合并请求/响应日志，便于管理后台展示。"""
        logs_dir = self._get_logs_dir(user_id)
        if not logs_dir.exists():
            return []

        grouped: Dict[str, Dict[str, Any]] = {}
        for log_file in logs_dir.glob("*.json"):
            data = self._load_log_file(log_file)
            if not data:
                continue

            request_id = str(data.get("request_id") or "").strip()
            if not request_id:
                continue

            pair = grouped.setdefault(
                request_id,
                {
                    "request_id": request_id,
                    "user_id": user_id,
                    "request": None,
                    "response": None,
                },
            )
            if data.get("type") == "request":
                pair["request"] = data
            elif data.get("type") == "response":
                pair["response"] = data

        merged: List[Dict[str, Any]] = []
        for pair in grouped.values():
            request = pair.get("request") or {}
            response = pair.get("response") or {}
            timestamp = request.get("timestamp") or response.get("timestamp")
            merged.append(
                {
                    "request_id": pair["request_id"],
                    "timestamp": timestamp,
                    "request": request,
                    "response": response,
                    "latency_ms": response.get("latency_ms"),
                    "parse_success": response.get("parse_success"),
                    "upstream_request_id": response.get("upstream_request_id"),
                    "attempts": response.get("attempts"),
                    "condition": request.get("condition"),
                    "model": response.get("model") or request.get("model"),
                    "state_snapshot": request.get("state_snapshot") or {},
                    "context_summary": request.get("context_summary") or {},
                    "outbound_summary": request.get("outbound_summary") or {},
                    "parsed_reply_preview": response.get("parsed_reply_preview") or "",
                    "parse_error": response.get("parse_error"),
                }
            )

        merged.sort(key=lambda item: _parse_iso(item.get("timestamp")), reverse=True)
        if limit and limit > 0:
            return merged[:limit]
        return merged


# 单例
_chat_logger: Optional[ChatLogger] = None

def get_chat_logger() -> ChatLogger:
    global _chat_logger
    if _chat_logger is None:
        _chat_logger = ChatLogger()
    return _chat_logger
