from __future__ import annotations

import json
import shutil
import tempfile
import threading
import traceback
import zipfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.chat_logger import get_chat_logger
from services.weekly_survey_service import sync_weekly_survey_records_for_user
from storage import JsonStorage


CHINA_TZ = timezone(timedelta(hours=8))


def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_BASE_PATH = PROJECT_ROOT / "memory" / "本体"
EXPORT_ROOT = PROJECT_ROOT / "zip" / "user_exports"
AVATAR_UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads" / "avatars"
MIN_USER_MESSAGE_LENGTH = 10


def _safe_avg(values: List[float]) -> float:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return 0.0
    return round(sum(nums) / len(nums), 2)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHINA_TZ)
        return dt
    except Exception:
        return None


def _week_key_from_iso(value: Optional[str]) -> Optional[str]:
    dt = _parse_iso(value)
    if not dt:
        return None
    return dt.strftime("%Y-W%W")


def _current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")


def _is_effective_assistant_message(message: dict) -> bool:
    if message.get("role") != "assistant":
        return False
    meta = message.get("meta") or {}
    segment_index = meta.get("segment_index")
    if segment_index is None:
        return True
    return segment_index == 0


def _sanitize_export_name(value: str, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        text = fallback
    for ch in '\\/:*?"<>|':
        text = text.replace(ch, "_")
    text = " ".join(text.split()).rstrip(".")
    return text or fallback


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
        suffix=".tmp",
    ) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_directory(source: Path, destination: Path) -> int:
    copied = 0
    for file in sorted(source.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(source)
        _copy_file(file, destination / relative)
        copied += 1
    return copied


def _clone_task_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    return deepcopy(task)


class UserExportService:
    def __init__(self, export_root: Optional[Path] = None):
        self.storage = JsonStorage()
        self.chat_logger = get_chat_logger()
        self.export_root = Path(export_root) if export_root else EXPORT_ROOT
        self.tasks_root = self.export_root / "tasks"
        self.tasks_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._live_tasks: Dict[str, Dict[str, Any]] = {}

    def normalize_user_ids(self, user_ids: List[int]) -> List[int]:
        normalized: List[int] = []
        seen = set()
        for value in user_ids:
            try:
                user_id = int(value)
            except Exception:
                continue
            if user_id <= 0 or user_id in seen:
                continue
            user = self.storage.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"用户 {user_id} 不存在")
            seen.add(user_id)
            normalized.append(user_id)
        if not normalized:
            raise ValueError("至少选择一位用户")
        return normalized

    def create_task(
        self,
        user_ids: List[int],
        *,
        admin_id: Optional[int] = None,
        requested_by: str = "admin",
        label: str = "",
    ) -> Dict[str, Any]:
        task = self._prepare_task(user_ids, admin_id=admin_id, requested_by=requested_by, label=label)
        with self._lock:
            self._live_tasks[task["task_id"]] = task
            self._persist_task_unlocked(task)
        thread = threading.Thread(
            target=self._run_task,
            args=(task["task_id"],),
            daemon=True,
            name=f"user-export-{task['task_id']}",
        )
        thread.start()
        return self.get_task(task["task_id"])

    def run_task_sync(
        self,
        user_ids: List[int],
        *,
        admin_id: Optional[int] = None,
        requested_by: str = "script",
        label: str = "",
    ) -> Dict[str, Any]:
        task = self._prepare_task(user_ids, admin_id=admin_id, requested_by=requested_by, label=label)
        with self._lock:
            self._live_tasks[task["task_id"]] = task
            self._persist_task_unlocked(task)
        self._run_task(task["task_id"])
        return self.get_task(task["task_id"])

    def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        tasks: List[Dict[str, Any]] = []
        for task_dir in self.tasks_root.iterdir():
            if not task_dir.is_dir():
                continue
            task_file = task_dir / "task.json"
            if not task_file.exists():
                continue
            try:
                task = json.loads(task_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            task = self._decorate_task_snapshot(task)
            task.pop("users", None)
            tasks.append(task)
        tasks.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return tasks[: max(1, min(limit, 200))]

    def get_task(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            live = self._live_tasks.get(task_id)
            if live:
                return self._decorate_task_snapshot(_clone_task_payload(live))

        task_file = self.tasks_root / task_id / "task.json"
        if not task_file.exists():
            raise FileNotFoundError(task_id)
        task = json.loads(task_file.read_text(encoding="utf-8"))
        return self._decorate_task_snapshot(task)

    def get_archive_path(self, task_id: str) -> Path:
        task = self.get_task(task_id)
        archive_path = Path(task.get("archive_path") or "")
        if task.get("status") != "completed" or not archive_path.exists():
            raise FileNotFoundError(task_id)
        return archive_path

    def _prepare_task(
        self,
        user_ids: List[int],
        *,
        admin_id: Optional[int],
        requested_by: str,
        label: str,
    ) -> Dict[str, Any]:
        normalized = self.normalize_user_ids(user_ids)
        now = get_china_now()
        task_id = f"export_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        task_dir = self.tasks_root / task_id
        package_name = f"用户全量原始数据_{now.strftime('%Y-%m-%d_%H-%M-%S')}"
        package_dir = task_dir / package_name
        archive_name = f"{package_name}.zip"
        archive_path = task_dir / archive_name

        users: List[Dict[str, Any]] = []
        for user_id in normalized:
            user = self.storage.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"用户 {user_id} 不存在")
            users.append(
                {
                    "user_id": user_id,
                    "username": user.get("username") or f"user_{user_id}",
                    "status": "pending",
                    "progress": 0,
                    "current_step": "等待开始",
                    "folder_name": "",
                    "exported_at": None,
                    "error": "",
                }
            )

        return {
            "task_id": task_id,
            "label": (label or "").strip(),
            "status": "queued",
            "requested_by": requested_by,
            "admin_id": admin_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "started_at": None,
            "finished_at": None,
            "overall_progress": 0,
            "processed_users": 0,
            "failed_users": 0,
            "total_users": len(users),
            "requested_user_ids": normalized,
            "current_user_id": None,
            "current_username": "",
            "current_step": "等待开始",
            "zip_progress": 0,
            "error_message": "",
            "task_dir": str(task_dir),
            "package_dir": str(package_dir),
            "archive_path": str(archive_path),
            "archive_name": archive_name,
            "archive_size_bytes": 0,
            "archive_exists": False,
            "users": users,
        }

    def _run_task(self, task_id: str) -> None:
        with self._lock:
            task = self._live_tasks.get(task_id)
            if not task:
                raise FileNotFoundError(task_id)
            task_dir = Path(task["task_dir"])
            package_dir = Path(task["package_dir"])
            task_dir.mkdir(parents=True, exist_ok=True)
            package_dir.mkdir(parents=True, exist_ok=True)
            task["status"] = "running"
            task["started_at"] = get_china_now().isoformat()
            task["current_step"] = "正在准备导出目录"
            self._touch_task_unlocked(task)

        try:
            self._write_package_manifest(task)
            for index, user_item in enumerate(task["users"]):
                self._export_single_user(task, index)

            with self._lock:
                task["status"] = "packaging"
                task["current_user_id"] = None
                task["current_username"] = ""
                task["current_step"] = "正在打包整个任务文件夹"
                task["zip_progress"] = 0
                self._recompute_progress_unlocked(task)
                self._touch_task_unlocked(task)

            self._zip_package_directory(task)

            with self._lock:
                archive_path = Path(task["archive_path"])
                task["status"] = "completed"
                task["finished_at"] = get_china_now().isoformat()
                task["current_step"] = "导出完成"
                task["current_user_id"] = None
                task["current_username"] = ""
                task["zip_progress"] = 100
                task["archive_exists"] = archive_path.exists()
                task["archive_size_bytes"] = archive_path.stat().st_size if archive_path.exists() else 0
                self._recompute_progress_unlocked(task)
                self._touch_task_unlocked(task)
        except Exception as exc:
            with self._lock:
                task["status"] = "failed"
                task["finished_at"] = get_china_now().isoformat()
                task["error_message"] = str(exc)
                if task.get("current_user_id") and task.get("users"):
                    for item in task["users"]:
                        if item.get("user_id") == task["current_user_id"] and item.get("status") == "running":
                            item["status"] = "failed"
                            item["error"] = str(exc)
                task["current_step"] = "导出失败"
                self._recompute_progress_unlocked(task)
                self._touch_task_unlocked(task)
            traceback.print_exc()

    def _write_package_manifest(self, task: Dict[str, Any]) -> None:
        manifest_path = Path(task["package_dir"]) / "manifest.json"
        manifest = {
            "task_id": task["task_id"],
            "created_at": task["created_at"],
            "requested_by": task["requested_by"],
            "admin_id": task["admin_id"],
            "label": task.get("label") or "",
            "user_count": task["total_users"],
            "user_ids": list(task["requested_user_ids"]),
        }
        _write_json_atomic(manifest_path, manifest)

    def _export_single_user(self, task: Dict[str, Any], user_index: int) -> None:
        user_progress = task["users"][user_index]
        user_id = int(user_progress["user_id"])
        user = self.storage.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"用户 {user_id} 不存在")

        sync_weekly_survey_records_for_user(user_id)

        username = str(user.get("username") or f"user_{user_id}")
        folder_name = f"{_sanitize_export_name(username, f'user_{user_id}')}_{user_id}"
        user_folder = Path(task["package_dir"]) / folder_name
        user_folder.mkdir(parents=True, exist_ok=True)

        with self._lock:
            user_progress["status"] = "running"
            user_progress["progress"] = 0
            user_progress["current_step"] = "开始导出用户数据"
            user_progress["folder_name"] = folder_name
            task["current_user_id"] = user_id
            task["current_username"] = username
            task["current_step"] = f"正在处理 {username}"
            self._recompute_progress_unlocked(task)
            self._touch_task_unlocked(task)

        history = self.storage.get_chat_history(user_id=user_id, limit=0)
        checkins = self.storage.get_checkin_records(user_id)
        logs = self.chat_logger.get_paired_logs(user_id, limit=0)
        prompt_events = self.storage.get_prompt_events(user_id=user_id, limit=100000)

        steps = [
            ("写入用户基本信息", lambda: _write_json_atomic(user_folder / "user.json", {k: v for k, v in user.items() if k != "pwd_hash"})),
            (
                "写入统计快照",
                lambda: _write_json_atomic(
                    user_folder / "metrics.json",
                    self._build_user_metrics(
                        user,
                        history=history,
                        checkins=checkins,
                        logs=logs,
                        prompt_events=prompt_events,
                    ),
                ),
            ),
            ("写入实验状态", lambda: _write_json_atomic(user_folder / "experiment_state.json", self.storage.get_user_experiment_state(user_id))),
            ("写入打卡记录", lambda: _write_json_atomic(user_folder / "checkins.json", checkins)),
            ("写入请求日志摘要", lambda: _write_json_atomic(user_folder / "request_logs.json", logs)),
            ("写入提示事件", lambda: _write_json_atomic(user_folder / "prompt_events.json", prompt_events)),
            ("写入提示状态", lambda: _write_json_atomic(user_folder / "prompt_states.json", self.storage.get_user_prompt_states(user_id))),
            ("写入通知记录", lambda: _write_json_atomic(user_folder / "notices.json", self.storage.get_inbox_notices_for_user(user_id))),
            ("写入通知状态", lambda: _write_json_atomic(user_folder / "notice_states.json", self.storage.get_user_notice_states(user_id))),
            ("写入周问卷记录", lambda: _write_json_atomic(user_folder / "weekly_surveys.json", self.storage.get_weekly_survey_records(user_id=user_id, limit=0))),
            ("写入聊天记录", lambda: _write_json_atomic(user_folder / "chat_history.json", history)),
            ("复制记忆目录", lambda: self._copy_memory_tree(user_id, user_folder / "memory")),
            ("复制头像文件", lambda: self._copy_avatar_file(user, user_folder / "avatar")),
        ]

        total_steps = len(steps)
        for offset, (step_name, action) in enumerate(steps, start=1):
            with self._lock:
                user_progress["current_step"] = step_name
                user_progress["progress"] = round(((offset - 1) / total_steps) * 100)
                task["current_step"] = f"{username}: {step_name}"
                self._recompute_progress_unlocked(task)
                self._touch_task_unlocked(task)
            action()
            with self._lock:
                user_progress["progress"] = round((offset / total_steps) * 100)
                self._recompute_progress_unlocked(task)
                self._touch_task_unlocked(task)

        with self._lock:
            user_progress["status"] = "completed"
            user_progress["progress"] = 100
            user_progress["current_step"] = "已完成"
            user_progress["exported_at"] = get_china_now().isoformat()
            task["processed_users"] += 1
            self._recompute_progress_unlocked(task)
            self._touch_task_unlocked(task)

    def _copy_memory_tree(self, user_id: int, destination: Path) -> None:
        source = MEMORY_BASE_PATH / str(user_id)
        destination.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            _write_json_atomic(destination / "memory_missing.json", {"exists": False, "user_id": user_id})
            return
        copied_files = _copy_directory(source, destination)
        if copied_files == 0:
            _write_json_atomic(destination / "memory_empty.json", {"exists": True, "user_id": user_id, "files": 0})

    def _copy_avatar_file(self, user: Dict[str, Any], destination: Path) -> None:
        avatar_url = str(user.get("avatar") or "").strip()
        destination.mkdir(parents=True, exist_ok=True)
        if not avatar_url.startswith("/uploads/avatars/"):
            _write_json_atomic(destination / "avatar_missing.json", {"avatar": avatar_url})
            return
        filename = avatar_url.split("/uploads/avatars/", 1)[1]
        source = AVATAR_UPLOAD_DIR / filename
        if not source.exists():
            _write_json_atomic(destination / "avatar_missing.json", {"avatar": avatar_url})
            return
        _copy_file(source, destination / source.name)

    def _zip_package_directory(self, task: Dict[str, Any]) -> None:
        package_dir = Path(task["package_dir"])
        archive_path = Path(task["archive_path"])
        file_list = [file for file in sorted(package_dir.rglob("*")) if file.is_file()]
        total_files = len(file_list)
        with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            if total_files == 0:
                zip_file.writestr(f"{package_dir.name}/EMPTY.txt", "export is empty")
            for index, file in enumerate(file_list, start=1):
                arcname = file.relative_to(package_dir.parent).as_posix()
                zip_file.write(file, arcname=arcname)
                with self._lock:
                    task["zip_progress"] = round((index / total_files) * 100) if total_files else 100
                    task["current_step"] = f"正在压缩 {file.name}"
                    self._recompute_progress_unlocked(task)
                    self._touch_task_unlocked(task)

    def _build_user_metrics(
        self,
        user: dict,
        *,
        history: Optional[List[Dict[str, Any]]] = None,
        checkins: Optional[List[Dict[str, Any]]] = None,
        logs: Optional[List[Dict[str, Any]]] = None,
        prompt_events: Optional[List[Dict[str, Any]]] = None,
    ) -> dict:
        user_id = user.get("id")
        if not isinstance(user_id, int):
            return {}

        history = list(history if history is not None else self.storage.get_chat_history(user_id=user_id, limit=0))
        checkins = list(checkins if checkins is not None else self.storage.get_checkin_records(user_id))
        logs = list(logs if logs is not None else self.chat_logger.get_paired_logs(user_id, limit=0))
        prompt_events = list(
            prompt_events
            if prompt_events is not None
            else self.storage.get_prompt_events(user_id=user_id, limit=100000)
        )

        exp_state = self.storage.get_user_experiment_state(user_id)
        settings = self.storage.get_settings()
        current_week = exp_state.get("current_week_key") or _current_week_key()

        user_messages = [m for m in history if m.get("role") == "user"]
        assistant_messages = [m for m in history if m.get("role") == "assistant"]
        effective_dialogues = [m for m in assistant_messages if _is_effective_assistant_message(m)]
        this_week_messages = [m for m in history if _week_key_from_iso(m.get("timestamp")) == current_week]
        this_week_effective_dialogues = [m for m in effective_dialogues if _week_key_from_iso(m.get("timestamp")) == current_week]
        this_week_checkins = [r for r in checkins if r.get("week_key") == current_week]
        parse_success_logs = [l for l in logs if l.get("parse_success") is True]
        latency_values = [l.get("latency_ms") for l in logs if isinstance(l.get("latency_ms"), (int, float))]
        min_length = int(settings.get("min_user_message_length", MIN_USER_MESSAGE_LENGTH) or MIN_USER_MESSAGE_LENGTH)

        return {
            "user_id": user_id,
            "username": user.get("username"),
            "condition": user.get("self_disclosure_condition", "none"),
            "created_at": user.get("created_at"),
            "message_count": len(history),
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "image_message_count": sum(1 for m in history if m.get("image")),
            "effective_dialogue_count": len(effective_dialogues),
            "this_week_message_count": len(this_week_messages),
            "this_week_effective_dialogue_count": len(this_week_effective_dialogues),
            "weekly_checkin_count": exp_state.get("weekly_checkin_count", 0),
            "required_weekly_checkins": int(settings.get("min_weekly_checkins_for_survey", 2) or 2),
            "total_checkin_count": len(checkins),
            "this_week_checkin_count": len(this_week_checkins),
            "avg_rounds_per_checkin": _safe_avg([r.get("round_count_at_checkin") for r in checkins]),
            "current_round_count": exp_state.get("current_round_count", 0),
            "last_user_message_time": exp_state.get("last_user_message_time"),
            "session_start_time": exp_state.get("session_start_time"),
            "last_session_end_time": exp_state.get("last_session_end_time"),
            "last_checkin_at": exp_state.get("last_checkin_at"),
            "current_week_key": current_week,
            "weekly_survey_popup_shown": exp_state.get("weekly_survey_popup_shown", False),
            "request_count": len(logs),
            "successful_request_count": len(parse_success_logs),
            "avg_latency_ms": _safe_avg(latency_values),
            "last_request_at": logs[0].get("timestamp") if logs else None,
            "prompt_event_count": len(prompt_events),
            "prompt_shown_count": sum(1 for e in prompt_events if e.get("event_type") == "shown"),
            "prompt_answered_count": sum(1 for e in prompt_events if e.get("event_type") == "answered"),
            "valid_user_message_count": sum(
                1 for m in user_messages if len(str(m.get("content") or "").strip()) >= min_length
            ),
        }

    def _recompute_progress_unlocked(self, task: Dict[str, Any]) -> None:
        total_users = max(int(task.get("total_users") or 0), 1)
        user_ratio_total = 0.9
        zip_ratio_total = 0.1

        user_progress_sum = 0.0
        for item in task.get("users", []):
            user_progress_sum += float(item.get("progress") or 0) / 100.0
            if item.get("status") == "failed":
                task["failed_users"] = sum(1 for user in task["users"] if user.get("status") == "failed")

        user_ratio = min(user_progress_sum / total_users, 1.0) * user_ratio_total
        zip_ratio = (float(task.get("zip_progress") or 0) / 100.0) * zip_ratio_total
        overall = round(min((user_ratio + zip_ratio) * 100, 100))

        if task.get("status") == "completed":
            overall = 100
        task["overall_progress"] = overall

    def _touch_task_unlocked(self, task: Dict[str, Any]) -> None:
        task["updated_at"] = get_china_now().isoformat()
        self._persist_task_unlocked(task)

    def _persist_task_unlocked(self, task: Dict[str, Any]) -> None:
        task_dir = Path(task["task_dir"])
        task_dir.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(task_dir / "task.json", task)

    def _decorate_task_snapshot(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task["archive_exists"] = bool(task.get("archive_path")) and Path(task["archive_path"]).exists()
        task["can_download"] = bool(task["archive_exists"] and task.get("status") == "completed")
        task["is_active"] = task.get("status") in {"queued", "running", "packaging"}
        return task


_export_service: Optional[UserExportService] = None


def get_export_service() -> UserExportService:
    global _export_service
    if _export_service is None:
        _export_service = UserExportService()
    return _export_service
