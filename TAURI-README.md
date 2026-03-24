# Tauri 桌面应用构建指南

## 环境准备

### 1. 安装 Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

### 2. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev libssl-dev libgtk-3-dev libsoup2.4-dev javascriptcoregtk-4.0
```

**macOS:**
```bash
# 安装 Xcode 命令行工具
xcode-select --install
```

**Windows:**
```powershell
# 安装 Microsoft Visual Studio C++ 生成工具
# 下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# 安装时选择 "使用 C++ 的桌面开发"
# 同时安装 WebView2 运行时
```

### 3. 安装 Tauri CLI
```bash
cargo install tauri-cli --version "^1.5"
```

## 运行开发模式

```bash
cd /home/DONG/Mycode/shinecaniep

cargo tauri dev
```

## 构建生产包

```bash
cargo tauri build
```

构建完成后，安装包位于：
- **Linux**: `src-tauri/target/release/bundle/deb/*.deb`
- **macOS**: `src-tauri/target/release/bundle/dmg/*.dmg`
- **Windows**: `src-tauri/target/release/bundle/msi/*.msi`

## 图标设置

将 `src/icon.ico` 转换为多种尺寸格式：
- `icons/32x32.png`
- `icons/128x128.png`
- `icons/128x128@2x.png`
- `icons/icon.icns` (macOS)
- `icons/icon.ico` (Windows)

可以使用在线工具生成： https://tauri.app/v1/guides/features/icons/

## 配置说明

### 窗口设置 (tauri.conf.json)
```json
"windows": [{
    "fullscreen": false,
    "height": 800,
    "width": 1400,
    "minWidth": 1024,
    "minHeight": 768,
    "center": true
}]
```

### 安全策略
已配置宽松的 CSP 策略以支持：
- 内联样式和脚本
- 远程图片加载
- WebSocket 连接
- 本地文件访问

## 常见问题

### 1. 页面空白
确保 `index.html` 在项目的根目录，且所有资源路径使用相对路径。

### 2. 跨域问题
Tauri 中不需要担心 `file://` 协议限制，已配置允许远程请求。

### 3. 图标不显示
检查 `src-tauri/icons/` 目录下是否有正确格式的图标文件。

## 打包快捷方式创建工具

如果要同时打包 Python 快捷方式创建工具，需要：
1. 将 Python 脚本编译为可执行文件
2. 在 Tauri 中通过 Command API 调用

或者保持为独立工具，在 README 中说明。
