# Smile-Chat - AI聊天系统

一个基于Vue3和FastAPI构建的现代化AI聊天应用，具有完整的用户管理、记忆系统和多API支持。

## 📋 项目概述

Smile-Chat（启明聊天）是一个功能完整的AI聊天系统，包含：
- 🤖 AI对话功能（支持多API自动切换）
- 👤 用户认证系统（邀请码注册）
- 💾 基于文件的记忆系统
- 🎨 现代化UI设计（响应式，支持PC和移动端）
- 🖼️ 头像上传和图片识别
- 📝 Markdown渲染
- 🔧 管理员面板

## 🏗️ 项目结构

```
Smile-Chat/
├── frontend/          # Vue3前端
│   ├── src/
│   │   ├── api/      # API接口封装
│   │   ├── pages/    # 页面组件
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
├── backend/           # FastAPI后端
│   ├── routers/      # API路由
│   ├── services/     # 业务服务
│   ├── utils/        # 工具函数
│   ├── models/       # 数据模型
│   ├── main.py       # 主入口
│   └── requirements.txt
├── memory/            # 记忆存储目录
│   └── 本体/
│       └── {user_id}/
│           ├── history/   # 聊天历史
│           ├── json/      # JSON记忆
│           └── memory/    # 长期记忆
└── uploads/           # 上传文件目录
    ├── avatars/      # 用户头像
    └── latest/       # 最新图片
```

## 🚀 快速开始

### 前置要求

- Node.js 16+
- Python 3.9+
- pip

### 1. 克隆项目

```bash
git clone <repository-url>
cd Smile-Chat
```

### 2. 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database.py

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写你的API密钥

# 运行后端服务器
python main.py
```

后端将在 http://localhost:8000 启动

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置API地址
cp .env.example .env

# 运行开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

### 4. 创建管理员账号

首先需要创建邀请码：

```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('data/smile_chat.db'); conn.execute('INSERT INTO invites (code) VALUES (\"admin-invite-123\")'); conn.commit()"
```

然后访问前端注册页面，使用邀请码 `admin-invite-123` 注册第一个账号（ID为1，自动成为管理员）。

## 📖 功能说明

### 用户端功能

- **登录/注册**: 邀请码注册机制，保证用户质量
- **AI聊天**: 
  - 实时对话
  - Markdown格式支持
  - 自动显示时间戳
  - 句子级流式渲染
- **个人设置**:
  - 头像上传
  - 查看/管理记忆
  - 聊天设置
- **侧边栏菜单**:
  - 聊天记录
  - 关于启明
  - 个人信息

### 管理员功能

- **用户管理**: 查看所有用户，重置密码
- **邀请码管理**: 批量生成邀请码
- **系统推送**: 向所有用户发送消息（开发中）

### AI服务特性

- **多API支持**: 配置主用API和多个备份API
- **自动切换**: API失败时自动切换到备份
- **记忆系统**: 
  - 聊天历史保存
  - JSON格式记忆
  - 长期记忆管理
  - 手动压缩功能

## 🎨 UI设计

UI参考设计图实现，采用明亮温暖的黄色主题：

- 顶部黄色标题栏"三 启明"
- 聊天气泡样式（类似微信/QQ）
- 黄色笑脸AI头像
- 星星装饰的输入框
- 响应式布局（PC和移动端适配）

## 🔧 配置说明

### 后端配置 (backend/config/api_channels.json)

```json
{
  "primary": {
    "name": "OpenAI",
    "base_url": "https://api.openai.com/v1",
    "api_key": "your-api-key",
    "model": "gpt-3.5-turbo"
  },
  "backup": [
    {
      "name": "备份API",
      "base_url": "https://...",
      "api_key": "...",
      "model": "..."
    }
  ],
  "system_prompt": "你是启明，一个友好的AI助手...",
  "enable_search": true
}
```

### 前端配置 (frontend/.env)

```env
VITE_API_URL=http://localhost:8000/api
```

## 📡 API文档

后端启动后访问 http://localhost:8000/docs 查看完整的API文档（Swagger UI）

主要接口：

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/chat/send` - 发送消息
- `GET /api/chat/history` - 获取历史
- `POST /api/user/avatar` - 上传头像
- `GET /api/memory/{user_id}` - 获取记忆
- `POST /api/admin/create_invite` - 创建邀请码

## 🚢 部署

### 后端部署（腾讯云LWS）

1. 安装依赖并初始化数据库
2. 配置 systemd 服务
3. 使用 Nginx 反向代理
4. 配置 HTTPS (Certbot)

### 前端部署

```bash
npm run build
```

将 `dist` 目录部署到静态服务器（Nginx）

## 📝 开发计划

详见 `plan.md` 文件

## 🛠️ 技术栈

**前端**:
- Vue 3 (Composition API)
- Vue Router 4
- Axios
- Marked (Markdown)
- Lucide Icons

**后端**:
- FastAPI
- SQLite
- JWT认证
- Passlib (密码哈希)
- HTTPx (异步HTTP)

## 📄 许可证

本项目仅供学习和个人使用。

## 👨‍💻 作者

Killer Best

---

**注意**: 
- 首次运行需要配置AI API密钥
- 管理员功能需要user_id为1的账号
- 生产环境部署前请修改JWT密钥和数据库配置
