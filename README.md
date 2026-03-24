# 资源教室管理系统 - IEP

一个用于资源教室管理的 Web 应用系统，配套快捷方式创建工具，支持跨平台桌面快捷方式生成。

## 项目结构

```
shinecaniep/
├── index.html              # 主应用页面（资源教室管理系统）
├── shortcut_creator.py     # 快捷方式创建工具 - 命令行版
├── shortcut_creator_gui.py # 快捷方式创建工具 - GUI版
├── shortcut-config.json    # 快捷方式配置文件
├── requirements.txt        # Python依赖
├── dist/                   # 构建输出目录
├── src/                    # 静态资源目录
│   ├── css/               # 样式文件（Tailwind CSS、Font Awesome）
│   ├── js/                # JavaScript 文件
│   │   └── tauri-api.js   # Tauri API 调用模块
│   ├── webfonts/          # 字体文件
│   └── icon.ico           # 应用图标
├── src-tauri/              # Tauri 桌面应用配置
│   ├── Cargo.toml         # Rust 依赖配置
│   ├── tauri.conf.json    # Tauri 应用配置
│   ├── src/               # Rust 源代码
│   │   └── main.rs        # 后端入口（包含自定义命令）
│   ├── icons/             # 应用图标
│   │   ├── 32x32.png
│   │   ├── 128x128.png
│   │   ├── 128x128@2x.png
│   │   ├── 256x256.png    # 新增
│   │   ├── icon.icns      # macOS 图标（新增）
│   │   ├── icon.ico       # Windows 图标
│   │   └── generate_icons.py  # 图标生成脚本（新增）
│   └── target/            # Rust 构建输出
└── README.md               # 项目说明文档
```

## 功能特性

### 1. 资源教室管理系统 (IEP)
- 基于 Web 的资源教室管理平台
- 使用 Tailwind CSS 构建现代化界面
- 集成 Font Awesome 图标库
- 响应式设计，支持多种屏幕尺寸

### 2. 快捷方式创建工具

#### 跨平台支持
- **Windows**: 创建 `.lnk` 快捷方式（需要 pywin32）或 `.bat` 批处理文件
- **macOS**: 创建 `.app` 应用包
- **Linux**: 创建 `.desktop` 桌面入口文件

#### 自动浏览器检测
- **Windows**: 360安全浏览器、360极速浏览器、Chrome、Edge、Firefox
- **macOS**: Safari、Chrome、Firefox、Edge、360安全浏览器
- **Linux**: Chrome、Chromium、Firefox、Edge、sensible-browser

#### 功能特点
- 自动检测系统已安装的浏览器
- 支持自定义快捷方式名称和目标页面
- 可选择图标文件（支持 .ico、.icns、.png、.svg 格式）
- 支持启动时最大化窗口选项
- 输出位置可选：桌面或脚本目录
- 配置保存和加载功能

## 安装要求

### 系统要求
- Python 3.6+
- Windows / macOS / Linux

### Python依赖
```bash
pip install -r requirements.txt
```

依赖包：
- `Pillow` - 图标预览功能（GUI版）
- `pywin32` - Windows快捷方式创建（可选，Windows平台）

## 使用方法

### GUI 版本（推荐）

```bash
python shortcut_creator_gui.py
```

界面操作：
1. 输入快捷方式名称
2. 指定目标页面（默认为 index.html）
3. 选择浏览器（自动检测或手动选择）
4. 选择图标文件（可选）
5. 勾选"启动时最大化窗口"（可选）
6. 选择输出位置（桌面或脚本目录）
7. 点击"创建快捷方式"按钮
8. 点击"保存配置"保存当前设置

### 命令行版本

```bash
python shortcut_creator.py
```

程序会自动：
1. 加载 `shortcut-config.json` 配置文件
2. 检测系统已安装的浏览器
3. 根据配置创建桌面快捷方式

### 配置文件说明

`shortcut-config.json` 示例：

```json
{
  "shortcut_name": "资源教室管理系统-IEP",
  "target_page": "index.html",
  "default_browser": "/usr/bin/sensible-browser",
  "default_browser_name": "sensible-browser",
  "start_maximized": true,
  "custom_icon": "src/icon.ico",
  "output_dir": "desktop",
  "browsers": {
    "windows": [...],
    "macos": [...],
    "linux": [...]
  }
}
```

配置项说明：
- `shortcut_name`: 快捷方式显示名称
- `target_page`: 目标 HTML 页面路径
- `default_browser`: 默认浏览器路径
- `default_browser_name`: 默认浏览器名称
- `start_maximized`: 是否以最大化窗口启动
- `custom_icon`: 自定义图标路径
- `output_dir`: 输出位置（"desktop" 或 "script"）
- `browsers`: 各平台浏览器配置列表

## 浏览器配置

### Windows 浏览器路径示例
```json
{
  "name": "Google Chrome",
  "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

### macOS 浏览器路径示例
```json
{
  "name": "Google Chrome",
  "path": "/Applications/Google Chrome.app"
}
```

### Linux 浏览器配置示例
```json
{
  "name": "Google Chrome",
  "command": "google-chrome"
}
```

## 技术栈

### 前端
- HTML5
- Tailwind CSS - 实用优先的 CSS 框架
- Font Awesome 6 - 图标库
- Google Fonts - Baloo Bhaijaan 字体

### 后端/工具
- Python 3.6+
- tkinter - GUI 界面
- pathlib - 跨平台路径处理
- subprocess - 系统命令调用

### 桌面应用
- Tauri v2 - Rust 驱动的桌面应用框架
- WebView2 / WKWebView / WebKitGTK - 系统级浏览器引擎

#### Tauri 后端功能
- **配置管理**: 读取/写入应用配置到本地存储
- **文件对话框**: 原生文件选择/保存对话框
- **快捷方式创建**: 跨平台桌面快捷方式生成
- **系统信息**: 获取操作系统信息
- **文件操作**: 读写文件、检查文件存在
- **命令执行**: 执行外部程序

## 平台特定说明

### Windows
- 推荐使用 `pywin32` 库创建标准快捷方式
- 未安装 pywin32 时会自动回退到批处理文件方案
- 使用注册表获取桌面路径

### macOS
- 创建标准的 `.app` 应用包结构
- 包含 `Info.plist` 和启动脚本
- 支持自定义图标

### Linux
- 创建符合 XDG 规范的 `.desktop` 文件
- 支持 `xdg-user-dir` 获取桌面路径
- 自动设置执行权限

## 注意事项

1. **图标格式**
   - Windows: 推荐使用 `.ico` 格式
   - macOS: 推荐使用 `.icns` 格式
   - Linux: 支持 `.png`、`.svg` 等格式

2. **权限问题**
   - Linux 平台创建的 `.desktop` 文件会自动设置可执行权限
   - macOS 应用包可能需要用户授权才能运行

3. **浏览器参数**
   - Windows Chrome/Edge 支持 `--start-maximized` 参数
   - 其他平台最大化行为可能因浏览器而异

## 许可证

MIT License

## Tauri 桌面应用

项目已配置 Tauri v2 桌面应用框架，可将 Web 应用打包为原生桌面应用。

### 项目结构
```
src-tauri/
├── Cargo.toml          # Rust 依赖配置
├── tauri.conf.json     # Tauri 应用配置
├── src/main.rs         # 后端入口
└── icons/              # 应用图标
```

### 运行开发模式
```bash
# 1. 安装 Rust（如果尚未安装）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. 安装 Tauri CLI
cargo install tauri-cli --version "^2.0.0-rc"

# 3. 安装系统依赖（Ubuntu/Debian）
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev libgdk-pixbuf2.0-dev \
    libatk1.0-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev

# 4. 启动 HTTP 服务器
python3 -m http.server 1420 --bind 127.0.0.1 &

# 5. 运行 Tauri 开发模式
cargo tauri dev
```

### 构建发布版本
```bash
cargo tauri build
```
构建产物位于 `src-tauri/target/release/bundle/`。

### Windows 快速运行
```bash
# 运行发布版本
.\运行Tauri应用.bat

# 或直接运行可执行文件
.\src-tauri\target\release\shinecaniep.exe
```

---

## 更新日志

### 2025-03-24
- **Tauri 后端功能完善**：
  - 添加 10+ 个自定义命令（配置读写、文件对话框、系统信息、快捷方式创建等）
  - 跨平台快捷方式创建 API（Windows .lnk / macOS .app / Linux .desktop）
  - 原生文件对话框集成到设置面板
  - 前端 Tauri API 模块 (`src/js/tauri-api.js`)
- **图标生成**：添加 `generate_icons.py` 脚本，自动生成 macOS icns 图标
- **网络检查优化**：修复 Tauri 环境下的网络状态检测
- **项目结构优化**：添加 `dist/` 目录用于构建

### 2025-03-19
- **平板适配优化**：添加针对 768px-1024px 平板设备的媒体查询，优化横竖屏显示
- **加载动画升级**：参考 QQ 官网风格，添加粒子连线 Canvas、流光线条、浮动光点、网格背景效果
- **Logo 透明化**：左上角 Logo 移除白色底色，支持透明 PNG
- **管理员验证**：设置按钮改为隐藏，需连续点击右上角热区 3 次并输入密码 (299451) 才能访问
- **Tauri 桌面应用**：配置 Tauri v2 框架，支持构建 Windows/macOS/Linux 原生桌面应用
- **安全优化**：检测 file:// 协议，避免本地文件模式下的安全警告

### 2024-03
- 初始版本发布
- 支持 Windows/macOS/Linux 三平台
- 提供 GUI 和命令行两种操作方式
