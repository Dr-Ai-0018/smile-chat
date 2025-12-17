"""
项目初始化脚本
快速设置数据库和创建初始管理员邀请码
"""
import argparse
import shutil
import sys
import secrets
from pathlib import Path

from storage import JsonStorage


def reset_project_data(storage: JsonStorage) -> None:
    base_dir = storage.base_dir
    memory_dir = Path(__file__).parent.parent / "memory" / "本体"

    if base_dir.exists():
        for item in base_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink(missing_ok=True)
                except Exception:
                    pass

    if memory_dir.exists():
        shutil.rmtree(memory_dir, ignore_errors=True)

    JsonStorage(base_dir=base_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)


def init_project(reset: bool = False, assume_yes: bool = False):
    print("=== Smile-Chat 项目初始化 ===\n")
    
    # 1. 初始化存储
    print("1. 初始化存储...")
    storage = JsonStorage()

    if reset:
        if not assume_yes:
            confirm = input(
                "将清空 backend/data/json 和 memory/本体 下的所有数据。\n"
                "请输入 YES 确认继续: "
            )
            if confirm.strip() != "YES":
                print("已取消")
                sys.exit(1)

        print("\n1.1 清空数据...")
        reset_project_data(storage)
        print("   ✓ 数据已清空")
    
    # 2. 创建管理员邀请码
    print("\n2. 创建管理员邀请码...")
    admin_code = "smile-admin-" + secrets.token_urlsafe(8)
    while True:
        created = storage.create_invite_codes([admin_code])
        if created:
            break
        admin_code = "smile-admin-" + secrets.token_urlsafe(8)
    
    print(f"   ✓ 管理员邀请码: {admin_code}")
    
    # 3. 创建额外的普通用户邀请码
    print("\n3. 创建5个普通用户邀请码...")
    user_codes = []
    while len(user_codes) < 5:
        code = "smile-user-" + secrets.token_urlsafe(12)
        created = storage.create_invite_codes([code])
        if created:
            user_codes.append(code)
    
    for i, code in enumerate(user_codes, 1):
        print(f"   {i}. {code}")
    
    # 4. 创建配置文件
    print("\n4. 创建配置文件...")
    config_dir = Path(__file__).parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    import json
    
    api_config = {
        "primary": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-3.5-turbo",
            "price": "$0.002/1K tokens"
        },
        "backup": [
            {
                "name": "Azure OpenAI",
                "base_url": "https://your-resource.openai.azure.com",
                "api_key_env": "AZURE_OPENAI_API_KEY",
                "model": "gpt-35-turbo",
                "price": "$0.002/1K tokens"
            }
        ],
        "system_prompt": "你是启明，一个友好、智能的AI聊天助手。请用简洁、温暖的语气回复用户。你善于倾听，理解用户的需求，并提供有帮助的建议。",
        "enable_search": True
    }
    
    config_file = config_dir / "api_channels.json"
    if not config_file.exists():
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(api_config, f, ensure_ascii=False, indent=2)
        print(f"   ✓ API配置文件: {config_file}")
    else:
        print(f"   ✓ API配置文件已存在: {config_file}")
    
    # 5. 创建必要的目录
    print("\n5. 创建必要的目录...")
    dirs = [
        Path(__file__).parent / "uploads" / "avatars",
        Path(__file__).parent / "uploads" / "latest",
        Path(__file__).parent.parent / "memory" / "本体",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}")
    
    print("\n" + "="*50)
    print("✅ 初始化完成！")
    print("\n下一步操作：")
    print("1. 编辑 backend/config/api_channels.json 填写你的API密钥")
    print("2. 运行 'python main.py' 启动后端服务器")
    print(f"3. 使用管理员邀请码注册第一个账号: {admin_code}")
    print("4. 第一个注册的用户(ID=1)将自动成为管理员")
    print("\n" + "="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    init_project(reset=args.reset, assume_yes=args.yes)
