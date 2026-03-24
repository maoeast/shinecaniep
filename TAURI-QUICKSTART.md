# Tauri 快速启动指南

## 项目结构

```
shinecaniep/
├── index.html              # 主页面
├── src/                    # CSS、字体、图标资源
├── src-tauri/              # Tauri 后端代码
│   ├── Cargo.toml         # Rust 依赖配置
│   ├── tauri.conf.json    # Tauri 应用配置
│   ├── build.rs           # 构建脚本
│   ├── src/main.rs        # 后端入口
│   └── icons/             # 应用图标
└── config.json            # 应用配置文件
```

## 首次运行

### 1. 安装 Rust（如果尚未安装）

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### 2. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y libwebkit2gtk-4.0-dev libssl-dev libgtk-3-dev \
    libsoup2.4-dev javascriptcoregtk-4.0 libappindicator3-dev
```

**macOS:**
```bash
xcode-select --install
```

**Windows:**
1. 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 安装 [WebView2 运行时](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

### 3. 安装 Tauri CLI

```bash
cargo install tauri-cli --version "^1.5"
```

### 4. 运行开发模式

```bash
cd /home/DONG/Mycode/shinecaniep
cargo tauri dev
```

首次运行会自动下载依赖并编译，可能需要几分钟。

### 5. 构建发布版本

```bash
cargo tauri build
```

构建产物：
- **Linux**: `src-tauri/target/release/bundle/deb/*.deb`
- **Windows**: `src-tauri/target/release/bundle/msi/*.msi`
- **macOS**: `src-tauri/target/release/bundle/dmg/*.dmg`

## 配置文件说明

### tauri.conf.json 关键配置

```json
{
  "tauri": {
    "windows": [{
      "title": "资源教室管理系统-IEP",
      "width": 1400,
      "height": 800,
      "minWidth": 1024,
      "minHeight": 768,
      "center": true,
      "resizable": true
    }],
    "security": {
      "csp": "..."  // 内容安全策略，已配置支持远程请求
    }
  }
}
```

### 适配修改

index.html 已添加 Tauri 检测：
```javascript
const isTauri = window.__TAURI__ !== undefined || window.location.protocol === 'tauri:';
```

在 Tauri 环境中：
- ✅ 正常加载 config.json
- ✅ localStorage 正常工作
- ✅ 无 file:// 协议限制

## 图标设置

已创建占位图标，构建前请替换：

```bash
# 如果你有 1024x1024 的源图
cargo install tauri-icon
tauri-icon /path/to/source/icon.png
```

或手动替换 `src-tauri/icons/` 下的文件。

## 常见问题

### 编译错误："error: linker `cc` not found"
```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install
```

### 运行错误："WebView2 not found"
```bash
# Windows 用户需安装 WebView2 运行时
# 下载地址：https://developer.microsoft.com/en-us/microsoft-edge/webview2/
```

### 应用启动后空白
检查 `tauri.conf.json` 中的 `devPath` 和 `distDir` 路径是否正确指向 index.html。

## 与 Python 工具的集成

如需在 Tauri 中调用 Python 快捷方式创建工具：

1. 将 Python 脚本打包为可执行文件（使用 PyInstaller）
2. 在 `src-tauri/tauri.conf.json` 中配置 sidecar
3. 使用 Tauri 的 Command API 调用

详见 TAURI-README.md
