"""
数据库配置和初始化
使用SQLite数据库
"""
from storage import JsonStorage

def get_db():
    """获取数据库连接"""
    storage = JsonStorage()
    yield storage

def init_db():
    """初始化数据库表"""
    JsonStorage()
    print("✓ 存储初始化完成")

if __name__ == "__main__":
    init_db()
