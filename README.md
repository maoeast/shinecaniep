# 资源教室管理系统 - IEP

基于 Tauri v2 构建的跨平台桌面应用，用于资源教室管理。

## 项目结构

```
shinecaniep/
├── index.html              # 主应用页面
├── config.json             # 应用配置文件
├── dist/                   # 构建输出目录
├── src/                    # 静态资源目录
│   ├── css/               # 样式文件（Tailwind CSS、Font Awesome）
│   ├── js/                # JavaScript 文件
│   │   └── tauri-api.js   # Tauri API 调用模块
│   ├── webfonts/          # 字体文件
│   └── icon.ico           # 应用图标
├── src-tauri/              # Tauri 后端
│   ├── Cargo.toml         # Rust 依赖配置
│   ├── tauri.conf.json    # Tauri 应用配置
│   ├── src/
│   │   └── main.rs        # 后端入口（自定义命令）
│   └── icons/             # 应用图标（多格式）
└── 运行Tauri应用.bat       # Windows 快速启动脚本
```

## 功能特性

### 资源教室管理系统
- 基于 Web 的资源教室管理平台
- Tailwind CSS 构建现代化界面
- Font Awesome 图标库
- 响应式设计，支持多种屏幕尺寸

### Tauri 桌面应用
- Tauri v2 构建原生桌面应用
- 右下角悬浮导航栏（返回、前进、刷新按钮）
- 登录后自动使用 iframe 加载外部网页
- 跨平台支持（Windows、macOS、Linux）
- 原生文件对话框集成
- 应用配置本地持久化存储

### Tauri 后端功能
- **配置管理**: 读取/写入应用配置到本地存储
- **文件对话框**: 原生文件选择/保存对话框
- **快捷方式创建**: 跨平台桌面快捷方式生成
- **系统信息**: 获取操作系统信息
- **文件操作**: 读写文件、检查文件存在
- **命令执行**: 执行外部程序

## 技术栈

### 前端
- HTML5
- Tailwind CSS
- Font Awesome 6

### 桌面应用
- Tauri v2 (Rust)
- WebView2 / WKWebView / WebKitGTK

## 开发

### 环境准备

1. 安装 [Rust](https://rustup.rs/)
2. 安装 Tauri CLI：
   ```bash
   cargo install tauri-cli --version "^2.0.0-rc"
   ```
3. Windows 需安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 和 [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

### 运行开发模式
```bash
cargo tauri dev
```

### 构建发布版本
```bash
cargo tauri build
```
构建产物位于 `src-tauri/target/release/bundle/`。

### Windows 快速运行
```bash
.\运行Tauri应用.bat
```

## 许可证

MIT License

## 更新日志

### 2025-03-26
- 新增右下角悬浮导航栏（返回、前进、刷新按钮）
- 登录后自动隐藏登录界面，使用 iframe 加载外部网页
- 新增 `webview_go_back`, `webview_go_forward`, `webview_reload` 后端命令
- 生成 NSIS 安装包

### 2025-03-24
- 添加 10+ 个自定义命令（配置读写、文件对话框、系统信息、快捷方式创建等）
- 前端 Tauri API 模块 (`src/js/tauri-api.js`)
- 修复 Tauri 环境下的网络状态检测

### 2025-03-19
- 平板适配优化
- 加载动画升级（粒子连线、流光线条等效果）
- 管理员验证（连续点击右上角热区 3 次 + 密码验证）
- Tauri v2 桌面应用框架配置

### 2024-03
- 初始版本发布
