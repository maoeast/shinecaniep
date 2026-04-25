# 资源中心综合评价管理平台

基于 Tauri v2 构建的跨平台桌面应用。

## 项目结构

```
shinecaniep/
├── build.js                # 打包前置配置脚本（系统名称一键同步）
├── dist/                   # 构建输出目录（唯一源文件目录）
│   ├── index.html         # 主应用页面（直接在此文件上开发）
│   └── config.json        # 应用默认配置（打包嵌入 + 首次启动复制到 exe 目录）
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
cd src-tauri && cargo tauri dev
```

### 打包发布流程

#### 第一步：配置系统名称

打开项目根目录下的 `build.js`，修改 `SYSTEM_NAME` 的值，然后运行脚本，即可自动将系统名称同步到三处打包相关文件：

```js
// build.js —— 只改这一处
const SYSTEM_NAME = '资源教室管理系统-IEP';
```

```bash
node build.js
```

脚本自动同步的三个文件：

| 文件 | 字段 |
|------|------|
| `dist/config.json` | `systemName` |
| `dist/index.html` | `<title>` |
| `src-tauri/Cargo.toml` | `description` |

> `build.js` 基于 Node.js 原生模块（`fs`、`path`），**Windows 和 Linux 均可直接运行**，无平台差异，前提是已安装 [Node.js](https://nodejs.org/)。

#### 第二步：清除编译缓存

**重要：** 修改 `dist/` 下的文件后，必须执行 `cargo clean` 清除缓存，否则改动不会被嵌入到打包产物中。

```bash
cd src-tauri && cargo clean
```

#### 第三步：打包

```bash
cargo tauri build
```

打包产物位于：

```
# Windows（NSIS 安装包）
src-tauri/target/release/bundle/nsis/系统名称_1.0.0_x64-setup.exe

# Linux
src-tauri/target/release/bundle/deb/系统名称_1.0.0_amd64.deb
src-tauri/target/release/bundle/appimage/系统名称_1.0.0_amd64.AppImage
```

> Tauri 需要在**目标平台上编译**，不支持直接从 Linux 交叉编译 Windows 安装包（反之亦然）。Windows 安装包请在 Windows 机器上执行打包命令。

NSIS 安装包已配置为简体中文界面，设置位于 `tauri.conf.json` 的 `bundle.windows.nsis.languages` 字段。

### Windows 快速运行
```bash
.\运行Tauri应用.bat
```

## 许可证

MIT License

## 更新日志

### 2026-04-25
- 新增 `build.js` 打包前置配置脚本，系统名称一键同步到 `dist/config.json`、`dist/index.html`、`src-tauri/Cargo.toml`，支持 Windows 和 Linux
- 清理代码中的调试日志（`console.log`），保留必要的错误日志（`console.error`）

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
