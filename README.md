# Smile-Chat

Smile-Chat（启明）是一个前后端分离的聊天系统，包含用户聊天端、管理员后台、打卡问卷、通知收件箱、提示系统和长期记忆能力。

项目主要用于持续对话场景，后端采用 FastAPI，前端采用 Vue 3，业务数据以 JSON 文件和用户目录的形式落盘，便于本地开发、实验部署和服务器迁移。

## 功能概览

### 用户端

- 注册、登录、邀请码开关
- 文本与图片聊天
- Markdown 消息展示
- 打卡问卷与周末问卷提醒
- 通知弹窗与收件箱
- 头像与基础设置

### 管理端

- 仪表盘与详细统计
- 用户管理与用户详情查看
- 批量导出用户原始数据
- 记忆查看与手动压缩
- 提示系统管理
- API / Context / 系统配置
- 打卡题目与每周清理

## 技术栈

- 前端：Vue 3、Vue Router、Vite、Axios
- 后端：FastAPI、Pydantic、httpx、JWT
- 存储：`backend/data/json/` + `memory/本体/` + `backend/uploads/`

## 目录结构

```text
Smile-Chat/
├── backend/
│   ├── config/                 # API 与上下文配置
│   ├── data/json/              # 用户、设置、聊天、打卡、提示等业务数据
│   ├── models/                 # Pydantic schema
│   ├── prompts/                # 系统提示词
│   ├── routers/                # FastAPI 路由
│   ├── services/               # AI、记忆、日志、状态服务
│   ├── storage/                # JSON 存储层
│   ├── utils/                  # JWT、密码等工具
│   ├── main.py                 # 后端入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
├── memory/
│   └── 本体/{user_id}/         # 用户记忆、历史文件、请求日志
├── data_management/            # 数据备份 / 重置 / 恢复脚本
├── reference/                  # 设计与交互参考
├── QUICKSTART.md               # 本地快速启动
├── DEPLOYMENT.md               # 服务器部署说明
└── README.md
```

## 本地开发

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端默认运行在 `http://127.0.0.1:8000`。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`。

### 3. 生产构建前端

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist/`。

## 配置说明

### AI 通道配置

AI 通道配置文件位于：

- `backend/config/api_channels.json`
- `backend/config/context_config.json`

推荐通过环境变量提供实际密钥和模型配置，例如：

```env
AI_PRIMARY_KEY=your_api_key
AI_PRIMARY_BASE_URL=https://api.openai.com/v1
AI_PRIMARY_MODEL=gpt-4.1-mini
```

### 重要数据目录

以下目录属于运行时数据，部署或迁移时应保留：

- `backend/data/json/`
- `memory/本体/`
- `backend/uploads/`

## 管理后台说明

管理员后台主要用于：

- 查看整体统计和用户明细
- 检查请求日志、打卡记录、提示事件
- 管理提示词和系统参数
- 调整打卡题目与每周清理
- 导出选中用户的全量原始数据快照

默认管理员判断目前仍是 `user_id == 1`。

## 数据管理脚本

`data_management/db_manager.py` 提供交互式数据管理功能：

- 备份当前数据
- 按不同模式重置数据
- 从历史备份恢复

适合本地实验和服务器维护时使用。

## 文档

- [快速启动](./QUICKSTART.md)
- [部署说明](./DEPLOYMENT.md)

## 说明

- 本项目当前以文件存储为主，不依赖 SQLite 作为主业务库。
- 管理后台与聊天主链路都依赖运行时配置，修改后请按部署方式重启服务或重新加载前端。
