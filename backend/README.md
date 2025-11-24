# Smile-Chat 后端

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python database.py
```

### 3. 创建管理员邀请码
```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 4. 配置API密钥
复制 `.env.example` 为 `.env` 并填写你的API密钥

### 5. 运行服务器
```bash
python main.py
```

服务器将在 http://localhost:8000 启动

## API文档
访问 http://localhost:8000/docs 查看完整的API文档
