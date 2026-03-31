import argparse
import json
import sys
from pathlib import Path
from typing import List


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.export_service import UserExportService


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


def _parse_user_ids(raw: str) -> List[int]:
    normalized = raw.replace("，", ",").replace("、", ",").replace("\t", " ").strip()
    if not normalized:
        return []

    parts: List[str] = []
    for chunk in normalized.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts.extend(token for token in chunk.split() if token)

    user_ids: List[int] = []
    seen = set()
    for item in parts:
        value = int(item)
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        user_ids.append(value)
    return user_ids


def _input_with_default(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    text = input(f"{prompt}{suffix}: ").strip()
    return text or default


def _collect_inputs(args: argparse.Namespace) -> tuple[List[int], str, str]:
    if args.user_ids:
        return [int(value) for value in args.user_ids], args.label, args.output_root

    if args.non_interactive:
        raise ValueError("非交互模式下必须传入 --user-ids")

    print("=== Smile-Chat 原始数据导出脚本 ===")
    print("留空可使用默认值；用户 ID 支持格式：1 2 3 或 1,2,3")

    user_ids: List[int] = []
    while not user_ids:
        try:
            raw_ids = input("请输入要导出的用户 ID: ").strip()
        except EOFError:
            raise ValueError("未读取到交互输入，请直接运行脚本后按提示输入，或显式传入 --user-ids")
        try:
            user_ids = _parse_user_ids(raw_ids)
        except Exception:
            print("用户 ID 输入有误，请输入正整数，例如 1 2 3")
            continue
        if not user_ids:
            print("至少需要输入一位用户 ID")

    label = _input_with_default("请输入任务标签（可选）", "")
    output_root = _input_with_default("请输入导出根目录（留空使用默认目录）", "")

    print("")
    print("即将开始导出：")
    print(f"- 用户 ID: {', '.join(str(user_id) for user_id in user_ids)}")
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
