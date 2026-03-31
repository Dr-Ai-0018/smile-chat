import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.export_service import UserExportService
from storage import JsonStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量导出用户原始数据到任务目录并生成 zip")
    parser.add_argument(
        "--user-ids",
        nargs="*",
        default=None,
        help="用户 ID 列表，支持空格分隔，例如 --user-ids 1 2 3；不传则进入交互输入",
    )
    parser.add_argument(
        "--label",
        default="",
        help="可选标签，会写入任务元数据；不传时可在交互模式下输入",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help="可选导出根目录，默认使用项目下的 zip/user_exports；不传时可在交互模式下输入",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="禁用交互输入；此时必须显式传入 --user-ids",
    )
    return parser.parse_args()


def _normalize_tokens(raw: str) -> List[str]:
    normalized = raw.replace("，", ",").replace("、", ",").replace("\t", " ").strip()
    if not normalized:
        return []

    tokens: List[str] = []
    for chunk in normalized.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        tokens.extend(token for token in chunk.split() if token)
    return tokens


def _invite_status_for_user(user: Dict[str, Any], invites_by_code: Dict[str, Dict[str, Any]]) -> tuple[str, bool]:
    invite_code = str(user.get("invite_code_used") or "").strip()
    user_id = user.get("id")

    if invite_code == "no_code":
        return "免邀请码", False
    if not invite_code:
        return "未记录邀请码", False

    invite = invites_by_code.get(invite_code)
    if not invite:
        return f"邀请码缺失({invite_code})", False

    used = bool(invite.get("used"))
    used_by = invite.get("used_by")
    if used and used_by == user_id:
        return f"已核验({invite_code})", True
    if used and used_by != user_id:
        return f"占用异常({invite_code} -> {used_by})", False
    return f"未标记已用({invite_code})", False


def _collect_detected_users() -> List[Dict[str, Any]]:
    storage = JsonStorage()
    invites_by_code = {}
    for invite in storage.read_invites():
        code = str(invite.get("code") or "").strip()
        if code:
            invites_by_code[code] = invite

    users = []
    for item in storage.read_users():
        user_id = item.get("id")
        if not isinstance(user_id, int):
            continue
        message_count = storage.count_chat_messages(user_id)
        invite_status, invite_verified = _invite_status_for_user(item, invites_by_code)
        users.append(
            {
                "id": user_id,
                "username": str(item.get("username") or f"user_{user_id}"),
                "created_at": str(item.get("created_at") or ""),
                "message_count": message_count,
                "has_messages": message_count > 0,
                "invite_status": invite_status,
                "invite_verified": invite_verified,
            }
        )
    users.sort(key=lambda item: item["id"])
    return users


def _print_user_preview(users: List[Dict[str, Any]], *, full: bool = False) -> None:
    total = len(users)
    if total == 0:
        print("当前没有探测到可导出的用户。")
        return

    with_messages = sum(1 for item in users if item.get("has_messages"))
    verified_invites = sum(1 for item in users if item.get("invite_verified"))
    print(f"已自动探测到 {total} 位用户。")
    print(f"- 其中有消息记录: {with_messages} 位")
    print(f"- 邀请码已核验: {verified_invites} 位")
    print("可输入 `all`、`msg`、`1-50`、`1,3,8-12`、`list`。范围按用户 ID 解析。")
    print("`all` = 真全选；`msg` = 全选所有有消息记录的用户。")

    display_users = users
    if not full and total > 30:
        display_users = users[:20] + users[-10:]

    print("-" * 96)
    print(f"{'ID':>4} | {'用户名':<22} | {'消息数':>6} | {'聊天':<4} | {'邀请码状态':<28} | 注册时间")
    print("-" * 96)
    for item in display_users:
        username = str(item["username"])
        if len(username) > 22:
            username = f"{username[:19]}..."
        has_messages = "是" if item.get("has_messages") else "否"
        invite_status = str(item.get("invite_status") or "-")
        if len(invite_status) > 28:
            invite_status = f"{invite_status[:25]}..."
        print(
            f"{item['id']:>4} | {username:<22} | {int(item.get('message_count') or 0):>6} | "
            f"{has_messages:<4} | {invite_status:<28} | {item['created_at'] or '-'}"
        )
    print("-" * 96)

    if not full and total > len(display_users):
        print(f"... 已省略中间 {total - len(display_users)} 位用户，输入 `list` 可查看完整列表。")


def _parse_user_selection(raw: str, users: List[Dict[str, Any]]) -> List[int]:
    tokens = _normalize_tokens(raw)
    if not tokens:
        return []

    user_ids = {int(item["id"]) for item in users}
    users_with_messages = {int(item["id"]) for item in users if item.get("has_messages")}
    selected: List[int] = []
    seen = set()

    for token in tokens:
        lower = token.lower()
        if lower == "all":
            for user_id in sorted(user_ids):
                if user_id not in seen:
                    seen.add(user_id)
                    selected.append(user_id)
            continue
        if lower in {"msg", "msgs", "hasmsg", "message", "messages", "active"}:
            for user_id in sorted(users_with_messages):
                if user_id not in seen:
                    seen.add(user_id)
                    selected.append(user_id)
            continue

        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                start, end = end, start
            for user_id in range(start, end + 1):
                if user_id in user_ids and user_id not in seen:
                    seen.add(user_id)
                    selected.append(user_id)
            continue

        user_id = int(token)
        if user_id in user_ids and user_id not in seen:
            seen.add(user_id)
            selected.append(user_id)

    return selected


def _input_with_default(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    text = input(f"{prompt}{suffix}: ").strip()
    return text or default


def _collect_inputs(args: argparse.Namespace) -> tuple[List[int], str, str]:
    users = _collect_detected_users()
    if not users:
        raise ValueError("当前没有探测到任何用户，无法创建导出任务")

    if args.user_ids:
        selection = " ".join(args.user_ids)
        try:
            user_ids = _parse_user_selection(selection, users)
        except Exception:
            raise ValueError("命令行 user_ids 格式无效，请使用 `all`、`1-50`、`1,3,8-12` 或明确 ID")
        if not user_ids:
            raise ValueError("命令行 user_ids 没有匹配到任何已存在用户")
        return user_ids, args.label, args.output_root

    if args.non_interactive:
        raise ValueError("非交互模式下必须传入 --user-ids")

    print("=== Smile-Chat 原始数据导出脚本 ===")
    _print_user_preview(users)

    user_ids: List[int] = []
    while not user_ids:
        try:
            raw_ids = input("请输入要导出的用户选择: ").strip()
        except EOFError:
            raise ValueError("未读取到交互输入，请直接运行脚本后按提示输入，或显式传入 --user-ids")
        if raw_ids.lower() == "list":
            _print_user_preview(users, full=True)
            continue
        try:
            user_ids = _parse_user_selection(raw_ids, users)
        except Exception:
            print("用户选择输入有误，请输入 `all`、`msg`、`1-50`、`1,3,8-12` 这类格式")
            continue
        if not user_ids:
            print("没有匹配到任何用户，请重新输入；可输入 `list` 查看完整用户列表。")

    label = _input_with_default("请输入任务标签（可选）", "")
    output_root = _input_with_default("请输入导出根目录（留空使用默认目录）", "")

    print("")
    print("即将开始导出：")
    print(f"- 用户 ID: {', '.join(str(user_id) for user_id in user_ids)}")
    selected_users = {int(item["id"]): item for item in users}
    selected_with_messages = sum(1 for user_id in user_ids if selected_users.get(user_id, {}).get("has_messages"))
    selected_verified_invites = sum(1 for user_id in user_ids if selected_users.get(user_id, {}).get("invite_verified"))
    print(f"- 选中用户中有消息记录: {selected_with_messages}/{len(user_ids)}")
    print(f"- 选中用户中邀请码已核验: {selected_verified_invites}/{len(user_ids)}")
    print(f"- 任务标签: {label or '(空)'}")
    print(f"- 导出根目录: {output_root or str(PROJECT_ROOT / 'zip' / 'user_exports')}")
    confirmed = _input_with_default("确认开始？输入 y 继续", "y").lower()
    if confirmed not in {"y", "yes"}:
        raise ValueError("已取消导出")

    return user_ids, label, output_root


def main() -> int:
    args = parse_args()
    try:
        user_ids, label, output_root_raw = _collect_inputs(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    output_root = Path(output_root_raw).resolve() if output_root_raw else None
    service = UserExportService(export_root=output_root)

    try:
        task = service.run_task_sync(
            user_ids,
            requested_by="server_script",
            label=label,
        )
    except Exception as exc:
        print(f"导出失败: {exc}", file=sys.stderr)
        return 1

    print("")
    print(json.dumps({
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "task_dir": task.get("task_dir"),
        "package_dir": task.get("package_dir"),
        "archive_path": task.get("archive_path"),
        "archive_name": task.get("archive_name"),
        "total_users": task.get("total_users"),
        "processed_users": task.get("processed_users"),
        "error_message": task.get("error_message"),
    }, ensure_ascii=False, indent=2))

    return 0 if task.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
