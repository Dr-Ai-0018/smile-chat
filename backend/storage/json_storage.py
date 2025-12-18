import json
import os
import tempfile
import threading
import time
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import fcntl  # type: ignore
except Exception:
    fcntl = None

try:
    import msvcrt  # type: ignore
except Exception:
    msvcrt = None


class JsonStorage:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or (Path(__file__).resolve().parent.parent / "data" / "json")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._locks: Dict[str, threading.RLock] = {}
        self._locks_guard = threading.Lock()

        self._chat_history_dir = self.base_dir / "chat_history"
        self._chat_history_dir.mkdir(parents=True, exist_ok=True)

        self._users_file = self.base_dir / "users.json"
        self._invites_file = self.base_dir / "invites.json"
        self._settings_file = self.base_dir / "settings.json"

    def _lockfile_path(self, path: Path) -> Path:
        return path.parent / f"{path.name}.lock"

    @contextmanager
    def _file_lock(self, path: Path, timeout_seconds: float = 10.0):
        lock_path = self._lockfile_path(path)
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(lock_path, "a+b") as lock_file:
            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"0")
                lock_file.flush()
                os.fsync(lock_file.fileno())

            start = time.time()
            while True:
                try:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    elif msvcrt is not None:
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() - start >= timeout_seconds:
                        raise TimeoutError(str(path))
                    time.sleep(0.05)

            try:
                yield
            finally:
                try:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    elif msvcrt is not None:
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass

    def _get_lock(self, path: Path) -> threading.RLock:
        key = str(path.resolve())
        with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.RLock()
                self._locks[key] = lock
            return lock

    @contextmanager
    def _lock_paths(self, paths: List[Path]):
        ordered_paths = sorted(paths, key=lambda x: str(x.resolve()))
        locks = [self._get_lock(p) for p in ordered_paths]
        for lock in locks:
            lock.acquire()
        try:
            with ExitStack() as stack:
                for p in ordered_paths:
                    stack.enter_context(self._file_lock(p))
                yield
        finally:
            for lock in reversed(locks):
                lock.release()

    def _read_json_unlocked(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _write_json_atomic_unlocked(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                dir=str(path.parent),
                prefix=path.name + ".",
                suffix=".tmp",
            ) as tmp:
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = tmp.name
            os.replace(tmp_path, path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def read_json(self, path: Path, default: Any) -> Any:
        lock = self._get_lock(path)
        with lock:
            with self._file_lock(path):
                return self._read_json_unlocked(path, default)

    def write_json_atomic(self, path: Path, data: Any) -> None:
        lock = self._get_lock(path)
        with lock:
            with self._file_lock(path):
                self._write_json_atomic_unlocked(path, data)

    def _read_users_data_unlocked(self) -> Dict[str, Any]:
        data = self._read_json_unlocked(self._users_file, {"next_id": 1, "items": []})
        if not isinstance(data, dict):
            data = {"next_id": 1, "items": []}
        if not isinstance(data.get("items"), list):
            data["items"] = []
        next_id = data.get("next_id")
        if not isinstance(next_id, int) or next_id < 1:
            data["next_id"] = 1
        return data

    def _read_invites_data_unlocked(self) -> Dict[str, Any]:
        data = self._read_json_unlocked(self._invites_file, {"items": []})
        if not isinstance(data, dict):
            data = {"items": []}
        if not isinstance(data.get("items"), list):
            data["items"] = []
        return data

    def _chat_history_file(self, user_id: int) -> Path:
        return self._chat_history_dir / f"{user_id}.json"

    def append_chat_message(
        self,
        user_id: int,
        role: str,
        content: str,
        image: Optional[str] = None,
        timestamp: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        path = self._chat_history_file(user_id)
        default = {"next_id": 1, "items": []}
        with self._lock_paths([path]):
            data = self._read_json_unlocked(path, default)
            if not isinstance(data, dict):
                data = default

            items = data.get("items")
            if not isinstance(items, list):
                items = []
                data["items"] = items

            next_id = data.get("next_id")
            if not isinstance(next_id, int) or next_id < 1:
                next_id = 1

            item = {
                "id": next_id,
                "role": role,
                "content": content,
                "image": image,
                "timestamp": timestamp or get_china_now().isoformat(),
                "meta": meta or {},
            }
            items.append(item)
            data["next_id"] = next_id + 1

            self._write_json_atomic_unlocked(path, data)
            return item

    def get_chat_history(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        path = self._chat_history_file(user_id)
        default = {"next_id": 1, "items": []}
        data = self.read_json(path, default)
        if not isinstance(data, dict):
            return []
        items = data.get("items")
        if not isinstance(items, list):
            return []
        if limit <= 0:
            return list(items)
        return list(items[-limit:])

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        for user in self.read_users():
            if user.get("id") == user_id:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        for user in self.read_users():
            if user.get("username") == username:
                return user
        return None

    def create_user(self, username: str, pwd_hash: str, invite_code_used: Optional[str] = None) -> Dict[str, Any]:
        with self._lock_paths([self._users_file]):
            data = self._read_users_data_unlocked()
            items = data["items"]
            for user in items:
                if user.get("username") == username:
                    raise ValueError("username_exists")

            user_id = data["next_id"]
            created_at = get_china_now().isoformat()
            # 按 user_id % 3 确定性分配实验条件
            conditions = ["none", "emotional", "factual"]
            condition = conditions[user_id % 3]
            
            user = {
                "id": user_id,
                "username": username,
                "pwd_hash": pwd_hash,
                "avatar": "",
                "invite_code_used": invite_code_used,
                "created_at": created_at,
                "self_disclosure_condition": condition,
            }
            items.append(user)
            data["next_id"] = user_id + 1
            self._write_json_atomic_unlocked(self._users_file, data)
            return user

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock_paths([self._users_file]):
            data = self._read_users_data_unlocked()
            items = data["items"]
            for user in items:
                if user.get("id") == user_id:
                    user.update(updates)
                    self._write_json_atomic_unlocked(self._users_file, data)
                    return user
        return None

    def delete_user(self, user_id: int) -> bool:
        with self._lock_paths([self._users_file]):
            data = self._read_users_data_unlocked()
            items = data["items"]
            new_items = [u for u in items if u.get("id") != user_id]
            if len(new_items) == len(items):
                return False
            data["items"] = new_items
            self._write_json_atomic_unlocked(self._users_file, data)
            return True
        return False

    def clear_chat_history(self, user_id: int) -> None:
        path = self._chat_history_file(user_id)
        default = {"next_id": 1, "items": []}
        self.write_json_atomic(path, default)

    def count_chat_messages(self, user_id: int) -> int:
        path = self._chat_history_file(user_id)
        default = {"next_id": 1, "items": []}
        data = self.read_json(path, default)
        if not isinstance(data, dict):
            return 0
        items = data.get("items")
        if not isinstance(items, list):
            return 0
        return len(items)

    def read_users(self) -> List[Dict[str, Any]]:
        default = {"next_id": 1, "items": []}
        data = self.read_json(self._users_file, default)
        if not isinstance(data, dict):
            return []
        items = data.get("items")
        if not isinstance(items, list):
            return []
        return list(items)

    def get_invite(self, code: str) -> Optional[Dict[str, Any]]:
        for invite in self.read_invites():
            if invite.get("code") == code:
                return invite
        return None

    def create_invite_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
        with self._lock_paths([self._invites_file]):
            data = self._read_invites_data_unlocked()
            items = data["items"]

            existing = {i.get("code") for i in items if isinstance(i, dict)}
            created = []
            created_at = get_china_now().isoformat()
            for code in codes:
                if code in existing:
                    continue
                invite = {
                    "code": code,
                    "used": False,
                    "used_by": None,
                    "created_at": created_at,
                }
                items.append(invite)
                existing.add(code)
                created.append(invite)
            self._write_json_atomic_unlocked(self._invites_file, data)
            return created

    def mark_invite_used(self, code: str, user_id: int) -> bool:
        with self._lock_paths([self._invites_file]):
            data = self._read_invites_data_unlocked()
            items = data["items"]
            for invite in items:
                if invite.get("code") == code:
                    if invite.get("used"):
                        return False
                    invite["used"] = True
                    invite["used_by"] = user_id
                    self._write_json_atomic_unlocked(self._invites_file, data)
                    return True
        return False

    def register_user(self, username: str, pwd_hash: str, invite_code: str) -> Dict[str, Any]:
        with self._lock_paths([self._users_file, self._invites_file]):
            users_data = self._read_users_data_unlocked()
            invites_data = self._read_invites_data_unlocked()

            for user in users_data["items"]:
                if user.get("username") == username:
                    raise ValueError("username_exists")

            invite = None
            for item in invites_data["items"]:
                if item.get("code") == invite_code:
                    invite = item
                    break

            if not invite or invite.get("used"):
                raise ValueError("invalid_invite")

            user_id = users_data["next_id"]
            created_at = get_china_now().isoformat()
            # 按 user_id % 3 确定性分配实验条件
            conditions = ["none", "emotional", "factual"]
            condition = conditions[user_id % 3]
            user = {
                "id": user_id,
                "username": username,
                "pwd_hash": pwd_hash,
                "avatar": "",
                "invite_code_used": invite_code,
                "created_at": created_at,
                "self_disclosure_condition": condition,
            }
            users_data["items"].append(user)
            users_data["next_id"] = user_id + 1

            invite["used"] = True
            invite["used_by"] = user_id

            self._write_json_atomic_unlocked(self._users_file, users_data)
            self._write_json_atomic_unlocked(self._invites_file, invites_data)
            return user

    def read_invites(self) -> List[Dict[str, Any]]:
        default = {"items": []}
        data = self.read_json(self._invites_file, default)
        if not isinstance(data, dict):
            return []
        items = data.get("items")
        if not isinstance(items, list):
            return []
        return list(items)

    # ==================== Settings ====================
    def get_settings(self) -> Dict[str, Any]:
        """Get global settings"""
        default = {"invite_code_enabled": True}
        data = self.read_json(self._settings_file, default)
        if not isinstance(data, dict):
            return default
        return data

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update global settings"""
        with self._lock_paths([self._settings_file]):
            data = self._read_json_unlocked(self._settings_file, {"invite_code_enabled": True})
            if not isinstance(data, dict):
                data = {"invite_code_enabled": True}
            data.update(updates)
            self._write_json_atomic_unlocked(self._settings_file, data)
            return data

    def is_invite_code_enabled(self) -> bool:
        """Check if invite code system is enabled"""
        settings = self.get_settings()
        return settings.get("invite_code_enabled", True)

    def register_user_no_invite(self, username: str, pwd_hash: str) -> Dict[str, Any]:
        """Register user without invite code (when invite system is disabled)"""
        with self._lock_paths([self._users_file]):
            users_data = self._read_users_data_unlocked()

            for user in users_data["items"]:
                if user.get("username") == username:
                    raise ValueError("username_exists")

            user_id = users_data["next_id"]
            created_at = get_china_now().isoformat()
            # 按 user_id % 3 确定性分配实验条件
            conditions = ["none", "emotional", "factual"]
            condition = conditions[user_id % 3]
            
            user = {
                "id": user_id,
                "username": username,
                "pwd_hash": pwd_hash,
                "avatar": "",
                "invite_code_used": "no_code",
                "created_at": created_at,
                "self_disclosure_condition": condition,
            }
            users_data["items"].append(user)
            users_data["next_id"] = user_id + 1

            self._write_json_atomic_unlocked(self._users_file, users_data)
            return user
