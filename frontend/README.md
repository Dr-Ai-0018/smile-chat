# Smile-Chat 前端

基于 Vue 3 + Vite 构建的AI聊天应用前端

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Vite** - 下一代前端构建工具
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP客户端
- **Marked** - Markdown渲染器

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并配置API地址：
```bash
cp .env.example .env
```

### 3. 运行开发服务器
```bash
npm run dev
```

应用将在 http://localhost:5173 启动

### 4. 构建生产版本
```bash
npm run build
```

## 功能特性

- ✅ 用户登录/注册
- ✅ 实时AI聊天
- ✅ Markdown渲染
- ✅ 头像上传
- ✅ 聊天历史
- ✅ 个人设置
- ✅ 管理员面板
- ✅ 响应式设计（PC/移动端适配）

## 页面结构

- `/login` - 登录页面
- `/register` - 注册页面
- `/chat` - 聊天主页面
- `/settings` - 个人设置
- `/admin` - 管理员面板

## 主题颜色

根据设计图使用的颜色方案：
- **主色调**: #FDD152 (黄色)
- **深色调**: #CCB11F (深黄色)
- **强调色**: #2B7AB3 (蓝色)
- **浅色调**: #B0DCE6 (浅蓝色)
- **文字色**: #000000 (黑色)
