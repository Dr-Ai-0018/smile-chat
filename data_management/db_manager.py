#!/usr/bin/env python3
"""
Smile-Chat 数据管理工具
功能：备份 / 重置 / 恢复 项目所有数据

使用方式：python data_management/db_manager.py
（在项目根目录或 data_management/ 目录下运行均可）
"""

import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── 路径定位 ──────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent          # e:\Project\Smile-Chat
BACKUP_DIR  = SCRIPT_DIR / "backups"
DATA_DIR    = PROJECT_DIR / "backend" / "data" / "json"
MEMORY_DIR  = PROJECT_DIR / "memory" / "本体"

CHINA_TZ = timezone(timedelta(hours=8))

def now_str() -> str:
    return datetime.now(CHINA_TZ).strftime("%Y%m%d_%H%M%S")

# ─── 终端颜色（跨平台） ────────────────────────────────────────────────────────

if sys.platform == "win32":
    os.system("color")   # 启用 Windows 10 ANSI 支持

R  = "\033[91m"   # 红
G  = "\033[92m"   # 绿
Y  = "\033[93m"   # 黄
B  = "\033[94m"   # 蓝
C  = "\033[96m"   # 青
W  = "\033[97m"   # 白
DIM = "\033[2m"   # 暗
RST = "\033[0m"   # 重置

def info(msg):  print(f"{G}[✓]{RST} {msg}")
def warn(msg):  print(f"{Y}[!]{RST} {msg}")
def error(msg): print(f"{R}[✗]{RST} {msg}")
def step(msg):  print(f"{C}[→]{RST} {msg}")
def dim(msg):   print(f"{DIM}{msg}{RST}")

# ─── 输入辅助 ──────────────────────────────────────────────────────────────────

def ask(prompt: str) -> str:
    """带提示的输入，Ctrl+C 时安全退出"""
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        main_menu()
        sys.exit(0)

def confirm(msg: str) -> bool:
    """确认操作（需要输入 yes）"""
    ans = ask(f"{Y}{msg}{RST}\n  输入 {R}yes{RST} 确认，其他任意键取消：")
    return ans.lower() == "yes"

def choose(options: list, prompt: str = "请选择") -> int:
    """
    显示编号选项，返回 0-based 索引。
    返回 -1 表示返回上级。
    """
    for i, opt in enumerate(options, 1):
        print(f"  {W}{i}{RST}. {opt}")
    print(f"  {DIM}0. 返回主菜单{RST}")
    while True:
        raw = ask(f"{B}{prompt}{RST} [0-{len(options)}]: ")
        if raw == "0":
            return -1
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        warn("无效选项，请重新输入")

# ─── 备份工具 ──────────────────────────────────────────────────────────────────

def _zip_data(zip_path: Path, label: str = "") -> None:
    """将 data/json 和 memory/本体 打包进 zip"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # backend/data/json  (排除 .lock 文件)
        if DATA_DIR.exists():
            for f in DATA_DIR.rglob("*"):
                if f.is_file() and not f.suffix == ".lock":
                    arcname = f.relative_to(PROJECT_DIR)
                    zf.write(f, arcname)

        # memory/本体
        if MEMORY_DIR.exists():
            for f in MEMORY_DIR.rglob("*"):
                if f.is_file():
                    arcname = f.relative_to(PROJECT_DIR)
                    zf.write(f, arcname)

        # 写入备份元信息
        meta = {
            "created_at": datetime.now(CHINA_TZ).isoformat(),
            "label": label,
            "files": zf.namelist(),
        }
        zf.writestr("_backup_meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

    size_kb = zip_path.stat().st_size // 1024
    info(f"备份完成 → {zip_path.name}  ({size_kb} KB，共 {len(zf.namelist())-1} 个文件)")


def do_backup(auto: bool = False, auto_label: str = "") -> Path:
    """
    执行备份操作。
    auto=True 时跳过交互，直接备份并返回路径。
    """
    if not auto:
        print(f"\n{W}=== 备份当前数据 ==={RST}")
        label = ask("备份备注（可为空，直接回车跳过）：")
    else:
        label = auto_label

    ts = now_str()
    zip_name = f"backup_{ts}.zip"
    if label:
        safe_label = label[:30].replace(" ", "_").replace("/", "-")
        zip_name = f"backup_{ts}_{safe_label}.zip"
    zip_path = BACKUP_DIR / zip_name

    step(f"正在打包数据到 {zip_path.name} ...")
    _zip_data(zip_path, label)
    return zip_path


# ─── 重置工具 ──────────────────────────────────────────────────────────────────

def _delete_chat_history():
    """清空所有聊天记录文件"""
    ch_dir = DATA_DIR / "chat_history"
    if ch_dir.exists():
        count = 0
        for f in ch_dir.glob("*.json"):
            f.unlink()
            count += 1
        step(f"已删除 {count} 个聊天记录文件")
    else:
        dim("  (chat_history 目录不存在，跳过)")


def _clear_json_file(filename: str, empty_value):
    """将某个 JSON 文件重置为空值"""
    p = DATA_DIR / filename
    if p.exists():
        p.write_text(json.dumps(empty_value, ensure_ascii=False, indent=2), encoding="utf-8")
        step(f"已清空 {filename}")
    else:
        dim(f"  ({filename} 不存在，跳过)")


def _delete_memory_data():
    """删除所有用户记忆目录"""
    if MEMORY_DIR.exists():
        count = 0
        for user_dir in MEMORY_DIR.iterdir():
            if user_dir.is_dir():
                shutil.rmtree(user_dir)
                count += 1
        step(f"已删除 {count} 个用户记忆目录")
    else:
        dim("  (memory/本体 目录不存在，跳过)")


def _reset_users():
    """清空用户数据（保留文件结构）"""
    _clear_json_file("users.json", {"next_id": 1, "items": []})
    _clear_json_file("invites.json", {"items": []})
    _clear_json_file("user_notice_states.json",  {})
    _clear_json_file("user_prompt_states.json",  {})
    _clear_json_file("prompt_events.json",       {"items": []})


RESET_MODES = [
    ("完全重置",   "清除所有用户账号、聊天记录、记忆（配置/设置保留）"),
    ("数据重置",   "保留用户账号，清除所有聊天记录和记忆"),
    ("仅聊天记录", "仅删除聊天记录，保留用户账号和记忆"),
]

def do_reset():
    print(f"\n{W}=== 重置数据 ==={RST}")
    warn("此操作不可逆！脚本会先自动备份当前数据。")
    print()

    print("请选择重置模式：")
    for i, (name, desc) in enumerate(RESET_MODES, 1):
        print(f"  {W}{i}{RST}. {R}{name}{RST} — {DIM}{desc}{RST}")
    print(f"  {DIM}0. 返回主菜单{RST}")

    while True:
        raw = ask(f"{B}请选择重置模式{RST} [0-{len(RESET_MODES)}]: ")
        if raw == "0":
            return
        if raw.isdigit() and 1 <= int(raw) <= len(RESET_MODES):
            mode_idx = int(raw) - 1
            break
        warn("无效选项，请重新输入")

    mode_name, mode_desc = RESET_MODES[mode_idx]
    print(f"\n已选择：{R}{mode_name}{RST} — {mode_desc}")

    if not confirm(f"确认执行「{mode_name}」？（此操作会先自动备份）"):
        info("已取消重置")
        return

    # 自动备份
    print()
    step("自动备份当前数据（重置前保护）...")
    backup_path = do_backup(auto=True, auto_label=f"auto_before_{mode_name}")
    print()

    # 执行重置
    step(f"开始执行「{mode_name}」...")

    if mode_idx == 0:   # 完全重置
        _reset_users()
        _delete_chat_history()
        _delete_memory_data()

    elif mode_idx == 1:  # 数据重置（保留用户）
        _delete_chat_history()
        _delete_memory_data()
        _clear_json_file("user_notice_states.json", {})
        _clear_json_file("user_prompt_states.json", {})
        _clear_json_file("prompt_events.json",      {"items": []})

    elif mode_idx == 2:  # 仅聊天记录
        _delete_chat_history()

    print()
    info(f"「{mode_name}」执行完毕！")
    info(f"备份已保存至：{backup_path}")


# ─── 恢复工具 ──────────────────────────────────────────────────────────────────

def _list_backups() -> list[Path]:
    """列出所有备份文件，按时间倒序"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = sorted(BACKUP_DIR.glob("backup_*.zip"), reverse=True)
    return backups


def _read_backup_meta(zip_path: Path) -> dict:
    """读取备份元信息"""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            if "_backup_meta.json" in zf.namelist():
                return json.loads(zf.read("_backup_meta.json"))
    except Exception:
        pass
    return {}


def _restore_from_zip(zip_path: Path) -> None:
    """从 zip 恢复数据（覆盖现有）"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if n != "_backup_meta.json"]
        step(f"共 {len(names)} 个文件待恢复")

        for name in names:
            dest = PROJECT_DIR / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))

    info("数据恢复完成！")


def _fmt_backup_info(zip_path: Path) -> str:
    """格式化备份显示行"""
    meta = _read_backup_meta(zip_path)
    size_kb = zip_path.stat().st_size // 1024
    created = meta.get("created_at", "未知时间")
    label   = meta.get("label", "")
    files   = len(meta.get("files", []))
    label_str = f"  [{label}]" if label else ""
    return f"{zip_path.name}{label_str}  ({size_kb} KB, {files} 文件, {created})"


def do_restore():
    print(f"\n{W}=== 从备份恢复 ==={RST}")

    backups = _list_backups()
    if not backups:
        warn("未找到任何备份文件。请先执行备份。")
        return

    print(f"找到 {len(backups)} 个备份（最新在前）：\n")
    options = [_fmt_backup_info(p) for p in backups]
    idx = choose(options, "选择要恢复的备份")
    if idx == -1:
        return

    selected = backups[idx]
    meta = _read_backup_meta(selected)

    print(f"\n已选择备份：{C}{selected.name}{RST}")
    if meta.get("label"):
        dim(f"  备注：{meta['label']}")
    dim(f"  备份时间：{meta.get('created_at', '未知')}")
    dim(f"  文件数量：{len(meta.get('files', []))}")
    print()

    warn("恢复操作会覆盖当前所有数据！建议先备份当前数据。")
    if confirm("恢复前是否先备份当前数据？"):
        do_backup(auto=True, auto_label="auto_before_restore")
        print()

    if not confirm(f"确认从「{selected.name}」恢复数据？"):
        info("已取消恢复")
        return

    print()
    step(f"正在从 {selected.name} 恢复...")
    _restore_from_zip(selected)
    info("恢复成功！如 backend 正在运行，建议重启服务使数据生效。")


# ─── 查看备份 ──────────────────────────────────────────────────────────────────

def do_list_backups():
    print(f"\n{W}=== 所有备份 ==={RST}")
    backups = _list_backups()
    if not backups:
        warn("暂无备份文件。")
        return

    total_kb = sum(p.stat().st_size for p in backups) // 1024
    print(f"备份目录：{BACKUP_DIR}")
    print(f"共 {len(backups)} 个备份，合计 {total_kb} KB\n")

    for i, p in enumerate(backups, 1):
        meta = _read_backup_meta(p)
        label = meta.get("label", "")
        created = meta.get("created_at", "")[:19].replace("T", " ")
        files = len(meta.get("files", []))
        size_kb = p.stat().st_size // 1024
        label_tag = f"  {DIM}[{label}]{RST}" if label else ""
        print(f"  {W}{i:2d}.{RST} {C}{p.name}{RST}{label_tag}")
        print(f"       {DIM}{created}  ·  {files} 个文件  ·  {size_kb} KB{RST}")

    print()
    ask("按回车返回主菜单...")


def do_delete_backup():
    print(f"\n{W}=== 删除备份 ==={RST}")
    backups = _list_backups()
    if not backups:
        warn("暂无备份文件。")
        return

    options = [_fmt_backup_info(p) for p in backups]
    idx = choose(options, "选择要删除的备份")
    if idx == -1:
        return

    selected = backups[idx]
    print(f"\n已选择：{R}{selected.name}{RST}")
    if not confirm(f"确认永久删除此备份文件？"):
        info("已取消删除")
        return

    selected.unlink()
    info(f"已删除 {selected.name}")


# ─── 主菜单 ────────────────────────────────────────────────────────────────────

def print_header():
    print(f"""
{C}╔══════════════════════════════════════════╗
║   Smile-Chat  数据管理工具                ║
╚══════════════════════════════════════════╝{RST}
  项目目录：{DIM}{PROJECT_DIR}{RST}
  备份目录：{DIM}{BACKUP_DIR}{RST}
""")

def main_menu():
    while True:
        print_header()
        options = [
            f"{G}备份当前数据{RST}          （手动创建备份）",
            f"{Y}重置数据{RST}              （自动备份后清除）",
            f"{B}从备份恢复{RST}            （选择备份覆盖当前）",
            f"{W}查看所有备份{RST}          （列出备份列表）",
            f"{R}删除某个备份{RST}          （释放磁盘空间）",
        ]
        print(f"{W}请选择操作：{RST}")
        for i, opt in enumerate(options, 1):
            print(f"  {W}{i}{RST}. {opt}")
        print(f"  {DIM}0. 退出{RST}\n")

        raw = ask(f"{B}请输入选项{RST} [0-{len(options)}]: ")

        if raw == "0":
            print(f"\n{DIM}再见！{RST}")
            sys.exit(0)
        elif raw == "1":
            do_backup()
        elif raw == "2":
            do_reset()
        elif raw == "3":
            do_restore()
        elif raw == "4":
            do_list_backups()
        elif raw == "5":
            do_delete_backup()
        else:
            warn("无效选项，请重新输入")

        print()


# ─── 入口 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{DIM}已退出{RST}")
        sys.exit(0)
