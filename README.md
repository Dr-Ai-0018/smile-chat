# Smile-Chat

Smile-Chat（启明）是一个围绕“AI 对话实验”构建的 Web 项目。  
它不只是一个普通聊天应用，而是把聊天、实验条件控制、提示系统、打卡问卷、周末问卷提醒、记忆管理和管理员后台整合到了一套前后端系统里。

---

## 项目概览

当前项目已经包含以下核心能力：

- 用户注册、登录、邀请码控制
- AI 聊天主链路
- 图片消息与 Markdown 渲染
- 自我表露实验条件切换
- 动态状态参数注入（preset）
- 提示系统（Prompt System）
- 通知系统（弹窗 + 收件箱）
- 打卡问卷与周末问卷提醒
- 长期记忆压缩与版本化管理
- 管理员后台（用户、记忆、邀请码、提示系统、打卡设置、上下文配置）

---

## 技术栈

### 前端

- Vue 3
- Vue Router 4
- Axios
- Marked
- DOMPurify
- Vite

### 后端

- FastAPI
- Pydantic
- JWT
- httpx
- python-dotenv

### 存储

当前项目的核心业务数据主要存放在：

1. `backend/data/json/`
   - 用户、邀请码、设置、聊天历史、提示系统、通知系统、实验状态、打卡记录
2. `memory/本体/{user_id}/`
   - 文本聊天历史、长期记忆、日志
3. `backend/uploads/`
   - 头像和上传图片

也就是说，项目当前是“**JSON 文件存储 + 文件系统记忆目录**”，不是旧版认知里的 SQLite 主存储方案。

---

## 当前功能地图

### 用户端

- 登录 / 注册
  - 支持邀请码制度开关
  - 用户名唯一校验

- 实验入口页
  - `/experiment/start`
  - 展示前测二维码和链接

- 聊天页
  - `/chat`
  - AI 多段回复流式展示
  - 图片发送
  - Prompt 弹窗
  - 打卡按钮与打卡弹窗
  - 通知弹窗与收件箱
  - 周末问卷提醒

- 设置页
  - `/settings`
  - 头像上传
  - 本地聊天设置

- 实验结束页
  - `/experiment/end`
  - 展示后测二维码和链接

### 管理员端

- 仪表盘统计
- 用户管理
- 记忆管理
- 邀请码管理
- 提示系统管理
- 上下文配置
- 打卡设置

---

## 实验功能主链路

### 1. 实验条件

用户创建时会按 `user_id % 3` 分配实验条件：

- `none`
- `emotional`
- `factual`

后端会根据条件加载不同提示词：

- `backend/prompts/无表露.txt`
- `backend/prompts/情感表露.txt`
- `backend/prompts/事实表露.txt`

### 2. AI 协议化输出

当前聊天主链路使用结构化 JSON 输出，核心字段包括：

- `reply`
- `segments`
- `did_self_disclosure`
- `relationship_stage_judge`

后端会：

1. 组装系统提示词、preset、长期记忆和近期对话
2. 请求上游模型
3. 解析结构化响应
4. 失败时自动修复重试
5. 记录请求/响应日志

### 3. preset 动态状态参数

每轮会注入给模型的状态参数包括：

- `recent_self_disclosure_rate`
- `last_relationship_stage`
- `conversation_duration_min`
- `local_time_bucket`
- `turn_count`
- `time_since_last_chat`

其中：

- `recent_self_disclosure_rate` 当前按“最近 5 轮对话”统计
- 若一次 API 回复被前端拆成多条 assistant 消息，仍只算同一轮
- 每轮只取最后一条 assistant 消息对应的自我表露标记

### 4. 打卡系统

打卡功能嵌在聊天页右上角。

当前规则：

- 用户消息达到最小长度阈值后，且 AI 成功完整回复，才算 1 轮
- 连续轮次达到阈值后开放打卡
- 打卡提交成功后才算一次有效打卡
- 打卡成功会清零当前轮次并进入冷却

默认实验参数：

```env
MIN_USER_MESSAGE_LENGTH=10
ROUND_RESET_INTERVAL_MINUTES=60
MIN_ROUNDS_FOR_CHECKIN=10
CHECKIN_COOLDOWN_HOURS=4
MIN_WEEKLY_CHECKINS_FOR_SURVEY=2
```

### 5. 周末问卷

当用户在当前自然周内完成足够次数的打卡后：

- 周六或周日上线时会自动检查周末问卷条件
- 首次满足条件时自动弹出一次提醒
- 同时写入用户专属 notice
- 后续不重复自动弹出，只能在收件箱里回看

### 6. 提示系统

提示系统是独立于 AI 主提示词之外的用户弹窗机制。

当前支持：

- 管理员创建 Prompt Group
- 配置阈值、频率、优先级、题型与内容
- 用户端在聊天后评估是否触发
- 记录 shown / answered / skipped 事件
- 管理员查看提示统计与回答

### 7. 通知系统

当前通知系统支持：

- 顶层弹窗通知
- 收件箱回看
- `shown_at` / `read_at` 用户状态
- 用户专属 notice

目前周末问卷就是基于这套 notice 系统承载的。

---

## 项目结构

```text
Smile-Chat/
├── backend/
│   ├── config/                 # API 与上下文配置
│   ├── models/                 # Pydantic schema
│   ├── prompts/                # 三套实验提示词
│   ├── routers/                # FastAPI 路由
│   ├── services/               # AI、记忆、状态、日志等服务
│   ├── storage/                # JSON 存储层
│   ├── utils/                  # JWT、密码等工具
│   ├── main.py                 # 后端入口
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/                # API 封装
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面
│   │   ├── utils/              # 前端工具
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── memory/
│   └── 本体/{user_id}/
│       ├── history/            # 文本聊天历史
│       ├── json/               # JSON 记忆
│       ├── ltm/                # 长期记忆版本
│       ├── memory/             # 兼容旧版长期记忆文本
│       └── logs/               # 每轮请求/响应日志
├── data_management/
│   └── db_manager.py           # 数据管理辅助脚本
├── reference/                  # 参考资料
├── 进阶实验功能.md             # 实验功能现状文档
├── DEPLOYMENT.md
├── QUICKSTART.md
└── README.md
```

---

## 关键后端模块

### 路由层

- `backend/routers/auth.py`
  - 注册、登录、邀请码制度状态

- `backend/routers/chat.py`
  - 聊天发送
  - 历史查询
  - 连续轮次统计
  - 会话结束时间记录

- `backend/routers/checkin.py`
  - 打卡状态
  - 打卡提交
  - 周末问卷检查
  - 打卡题目读取

- `backend/routers/prompts.py`
  - 提示系统用户端与管理员端接口

- `backend/routers/notices.py`
  - 通知系统用户端与管理员端接口

- `backend/routers/admin.py`
  - 用户、记忆、邀请码、统计、设置等管理员能力

### 服务层

- `backend/services/ai_service.py`
  - AI 请求主服务
  - 多 API 自动切换
  - 结构化输出
  - 记忆压缩

- `backend/services/session_state.py`
  - 计算 preset

- `backend/services/prompt_manager.py`
  - 按实验条件加载提示词

- `backend/services/response_parser.py`
  - 解析模型 JSON 输出并做兜底

- `backend/services/memory_service.py`
  - 长期记忆版本管理

- `backend/services/chat_logger.py`
  - 记录请求/响应日志

### 存储层

`backend/storage/json_storage.py` 当前统一管理：

- 用户
- 邀请码
- 设置
- 聊天历史
- 提示组与提示事件
- notice 与用户 notice 状态
- 实验状态
- 打卡记录

---

## 数据文件说明

当前 `backend/data/json/` 下的重要文件包括：

- `users.json`
- `invites.json`
- `settings.json`
- `chat_history/{user_id}.json`
- `prompt_groups.json`
- `user_prompt_states.json`
- `prompt_events.json`
- `notices.json`
- `user_notice_states.json`
- `user_experiment_states.json`
- `checkin_records.json`

实验功能相关状态字段至少包括：

- `current_round_count`
- `last_user_message_time`
- `session_start_time`
- `last_session_end_time`
- `last_checkin_at`
- `weekly_checkin_count`
- `weekly_survey_popup_shown`
- `current_week_key`

---

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+
- npm

### 1. 克隆项目

```bash
git clone <repository-url>
cd Smile-Chat
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

或使用：

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

默认启动地址：

- `http://localhost:8000`

Swagger 文档：

- `http://localhost:8000/docs`

### 3. 启动前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认前端地址：

- `http://localhost:5173`

### 4. 构建前端

```bash
cd frontend
npm run build
```

---

## 管理员初始化

当前项目已经不需要再用旧版 SQLite 命令手工插邀请码。

后端启动时，如果系统还是空数据：

1. 会自动生成一个管理员邀请码
2. 控制台会打印邀请码
3. 第一个注册成功的用户（`ID=1`）拥有管理员权限

你也可以通过环境变量自动创建管理员账号：

```env
BOOTSTRAP_ON_STARTUP=1
INIT_ADMIN_INVITE_CODE=your-admin-invite
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_PASSWORD=your-password
```

---

## 配置说明

### 后端 `.env`

`backend/.env.example` 当前至少包含：

```env
SECRET_KEY=your-secret-key-change-this-in-production
OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_API_KEY=your-azure-api-key
```

### AI 配置文件

后端主要读取：

- `backend/config/api_channels.json`
- `backend/config/context_config.json`

其中：

- `api_channels.json` 管理主模型、备份模型、API 类型、Base URL、模型名等
- `context_config.json` 管理上下文消息条数、token 限制、图片轮次等

此外，AI 配置还支持环境变量覆盖，例如：

- `AI_PRIMARY_NAME`
- `AI_PRIMARY_BASE_URL`
- `AI_PRIMARY_MODEL`
- `AI_PRIMARY_API_KEY`
- `AI_PRIMARY_API_KEY_ENV`
- `AI_ENABLE_SEARCH`
- `AI_CONTEXT_MAX_MESSAGES`
- `AI_CONTEXT_MAX_TOKENS`

### 前端 `.env`

```env
VITE_API_URL=http://localhost:8000/api
```

---

## 主要 API 模块

### 认证

- `GET /api/auth/invite_code_status`
- `POST /api/auth/register`
- `POST /api/auth/login`

### 聊天

- `POST /api/chat/send_with_context`
- `POST /api/chat/send`
- `GET /api/chat/history`

### 用户

- `GET /api/user/profile`
- `POST /api/user/avatar`

### 记忆

- `GET /api/memory/{user_id}`
- `POST /api/memory/update`
- `POST /api/memory/compress`

### 提示系统

- `POST /api/prompts/evaluate`
- `POST /api/prompts/{group_id}/shown`
- `POST /api/prompts/{group_id}/answer`
- `POST /api/prompts/{group_id}/skip`
- `POST /api/prompts/reset-counter`
- `GET /api/admin/prompt-groups`
- `POST /api/admin/prompt-groups`
- `PUT /api/admin/prompt-groups/{group_id}`
- `DELETE /api/admin/prompt-groups/{group_id}`

### 通知系统

- `GET /api/notices/pending`
- `GET /api/notices/inbox`
- `POST /api/notices/{notice_id}/shown`
- `POST /api/notices/{notice_id}/read`

### 打卡系统

- `GET /api/checkin/status`
- `POST /api/checkin/submit`
- `GET /api/checkin/weekend_survey_check`
- `GET /api/checkin/questions`

### 管理员

- `GET /api/admin/users`
- `GET /api/admin/stats`
- `POST /api/admin/create_invite`
- `GET /api/admin/invites`
- `POST /api/admin/reset_password`
- `GET /api/admin/memory/all`
- `GET /api/admin/settings`
- `PUT /api/admin/settings`

---

## 管理员后台现状

当前前端管理员后台已经有以下 tab：

- 仪表盘
- 用户管理
- 记忆管理
- 提示系统
- 邀请码
- 系统配置
- 打卡设置

其中：

- 打卡设置支持配置 `weekly_survey_url` 和 `checkin_questions`
- 提示系统支持 Prompt Group 管理与回答查看
- 用户管理支持看历史、看记忆、重置密码、删除用户

说明：

- 后端 notice 管理接口已经存在
- 但当前前端管理员页没有单独的通知管理 tab

---

## 开发与调试建议

### 1. 先看这几个入口文件

- 前端路由入口：`frontend/src/main.js`
- 聊天页面主逻辑：`frontend/src/pages/Chat.vue`
- 后端应用入口：`backend/main.py`
- AI 主服务：`backend/services/ai_service.py`
- JSON 存储层：`backend/storage/json_storage.py`

### 2. 实验功能优先看这几块

- 实验状态计算：`backend/services/session_state.py`
- 打卡接口：`backend/routers/checkin.py`
- 通知接口：`backend/routers/notices.py`
- 提示系统：`backend/routers/prompts.py`
- 实验文档：`进阶实验功能.md`

### 3. 调试日志位置

每个用户的聊天请求和响应日志会写到：

```text
memory/本体/{user_id}/logs/
```

这对排查：

- 模型原始输出
- parse 失败
- latency
- preset 注入
- 实验条件判断

很有帮助。

---

## 部署

### 前端

```bash
cd frontend
npm run build
```

将 `frontend/dist/` 部署到静态服务器即可。

### 后端

可以使用 `uvicorn` + 反向代理部署，例如 Nginx。

项目根目录已包含：

- `DEPLOYMENT.md`
- `nginx.conf`

部署前至少要确认：

1. `SECRET_KEY` 已替换
2. API Key 已配置
3. CORS 域名已按实际环境调整
4. 数据目录与上传目录有写权限

---

## 当前 README 与旧认知的主要差异

这份 README 已按当前代码实现更新，和旧版相比，最重要的修正包括：

1. 项目当前主存储是 JSON + 文件系统，不是 SQLite 主链路
2. 管理员初始化已经改为启动时自动 bootstrap
3. 项目已包含提示系统、通知系统、打卡系统、周末问卷链路
4. 管理员后台已包含打卡设置和提示系统配置
5. 聊天主链路已是结构化 JSON 输出，不是纯文本单回复模式

---

## 相关文档

- [进阶实验功能.md](./进阶实验功能.md)
- [QUICKSTART.md](./QUICKSTART.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
- [进一步开发.md](./进一步开发.md)

---

## 许可证

本项目仅供学习、研究和实验使用。
