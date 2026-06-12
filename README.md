# 资源教室管理系统-IEP

基于 Tauri v2 构建的跨平台桌面/平板应用，开发公司：杭州炫灿科技有限公司。

## 项目结构

```
shinecaniep/
├── build.js                     # 打包前置配置脚本（系统名称一键同步）
├── build_apk_cli.py             # APK 打包命令行工具（WSL/Linux 推荐）
├── build_apk_gui.py             # APK 打包 GUI 工具（Windows 推荐）
├── generate_android_icons.py    # Android APK 图标生成脚本
├── dist/                        # 构建输出目录（唯一源文件目录）
│   ├── index.html              # 主应用页面（直接在此文件上开发）
│   └── config.json             # 应用默认配置（打包嵌入 + 首次启动复制到 exe 目录）
├── src/                         # 静态资源目录
│   ├── css/                    # 样式文件（Tailwind CSS、Font Awesome）
│   ├── js/                     # JavaScript 文件
│   │   └── tauri-api.js        # Tauri API 调用模块
│   ├── webfonts/               # 字体文件
│   └── icon.ico                # 应用图标
├── src-tauri/                   # Tauri 后端
│   ├── Cargo.toml              # Rust 依赖配置
│   ├── tauri.conf.json         # Tauri 应用配置
│   ├── src/
│   │   ├── main.rs             # 桌面端入口
│   │   └── lib.rs              # 共享逻辑 + Android 入口
│   ├── gen/android/            # Android 项目（自动生成）
│   │   └── app/src/main/
│   │       ├── AndroidManifest.xml    # Android 权限声明
│   │       ├── java/.../MainActivity.kt  # Android 入口 Activity
│   │       └── res/
│   │           ├── mipmap-*/          # 应用图标（各密度）
│   │           ├── values/strings.xml # 应用名称
│   │           └── values/themes.xml  # 主题样式
│   ├── icons/                  # 桌面端图标（多格式，Android 不使用此目录）
│   └── target/                 # 编译输出
├── shinecaniep-release.jks     # Android APK 签名密钥库
└── 运行Tauri应用.bat            # Windows 快速启动脚本
```

## 功能特性

### 资源教室管理系统
- 基于 Web 的资源教室管理平台
- Tailwind CSS 构建现代化界面
- Font Awesome 图标库
- 支持桌面端和平板端

### Tauri 桌面应用
- Tauri v2 构建原生桌面应用
- 右下角悬浮导航栏（返回、前进、刷新按钮）
- 登录后导航至外部网页（无 iframe）
- 跨平台支持（Windows、macOS、Linux）
- 原生文件对话框集成
- 应用配置本地持久化存储

### Android 平板应用
- Tauri v2 Android 构建，支持 APK / AAB 输出
- 1280px 桌面视口，适配高分辨率平板（2560×1600、2800×1840 等）
- 支持双指缩放
- 摄像头、麦克风、蓝牙硬件访问（运行时权限自动请求）

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

### 移动端
- Tauri v2 Android
- Android WebView
- 目标设备：Android 平板（minSdk 24, targetSdk 36）

## 开发

### 环境准备

#### 桌面端
1. 安装 [Rust](https://rustup.rs/)
2. 安装 Tauri CLI：
   ```bash
   cargo install tauri-cli --version "^2.0.0"
   ```
3. Windows 需安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 和 [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

#### Android 端
在桌面端基础上，还需：
1. 安装 Android SDK（通过 Android Studio 或命令行工具）
2. 安装 NDK（推荐 28.x）
3. 添加 Android targets：
   ```bash
   rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
   ```
4. 初始化 Android 项目（仅首次）：
   ```bash
   cargo tauri android init
   ```
5. 图标生成（首次或更换图标后）：
   ```bash
   python generate_android_icons.py
   ```

### 运行开发模式
```bash
cd src-tauri && cargo tauri dev
```

### 打包发布流程

#### 桌面端（Windows）

##### 第一步：配置系统名称

打开项目根目录下的 `build.js`，修改 `SYSTEM_NAME` 的值，然后运行脚本：

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

> `build.js` 基于 Node.js 原生模块（`fs`、`path`），**Windows 和 Linux 均可直接运行**。

##### 第二步：清除编译缓存

**重要：** 修改 `dist/` 下的文件后，必须执行 `cargo clean` 清除缓存，否则改动不会被嵌入到打包产物中。

```bash
cd src-tauri && cargo clean
```

##### 第三步：打包

```bash
cd src-tauri && cargo tauri build
```

打包产物：

```
# Windows（NSIS 安装包）
src-tauri/target/release/bundle/nsis/系统名称_1.0.0_x64-setup.exe
```

> Tauri 需要在**目标平台上编译**。NSIS 安装包已配置为简体中文界面。

#### Android 端（APK）

##### 第一步：配置应用信息

Android APK 的元数据分散在多个文件中，以下为配置对照表：

| 配置项 | 文件 | 字段 | 当前值 |
|--------|------|------|--------|
| 应用名称 | `gen/android/.../res/values/strings.xml` | `app_name` | 资源教室管理系统-IEP |
| 包名 | `gen/android/.../build.gradle.kts` | `applicationId` | com.hzxckj.shinecan.iep |
| 版本号 | `tauri.conf.json` → 自动映射 | `version` | 1.0.3 |
| 公司名 | `tauri.conf.json` | `copyright` | 杭州炫灿科技有限公司 |
| 应用图标 | `gen/android/.../res/mipmap-*/` | PNG 文件 | 需手动生成 |

> ⚠️ `tauri.conf.json` 的 `bundle.icon` 仅用于桌面端。Android 图标位于 `gen/android/app/src/main/res/mipmap-*/`，**不会自动同步**。

##### 第二步：生成应用图标

```bash
python generate_android_icons.py
```

交互式输入（括号内为默认值，回车跳过）：

```
==================================================
  Android APK Icon Generator
==================================================

  Source icon path [src-tauri/icons/256x256.png]:     ← 源图标路径
  Android res dir [src-tauri/.../res]:                ← 自动检测，回车确认
  Background color [transparent]:                     ← transparent / #FFFFFF / 自定义
```

生成的文件（共 16 个）：

| 密度 | ic_launcher | ic_launcher_foreground | ic_launcher_round |
|------|-------------|------------------------|-------------------|
| mdpi | 48×48 | 108×108 | 48×48 |
| hdpi | 72×72 | 162×162 | 72×72 |
| xhdpi | 96×96 | 216×216 | 96×96 |
| xxhdpi | 144×144 | 324×324 | 144×144 |
| xxxhdpi | 192×192 | 432×432 | 192×192 |

> **注意**：更换 `tauri.conf.json` → `identifier` 后重新运行 `cargo tauri android init`，整个 `gen/android/` 目录会重新生成，需要重新运行此脚本。

##### 第三步：同步 dist 文件

确保 `dist/index.html` 是最新的。修改 `dist/` 后需触发重编译：

```bash
cd src-tauri && touch src/main.rs
```

##### 第四步：构建 APK

```bash
cd src-tauri && cargo tauri android build
```

构建产物：
- APK: `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release-unsigned.apk`
- AAB: `src-tauri/gen/android/app/build/outputs/bundle/universalRelease/app-universal-release.aab`

##### 第五步：签名 APK

```bash
# 对齐
zipalign -f 4 <unsigned.apk> <aligned.apk>

# 签名
apksigner sign \
  --ks shinecaniep-release.jks \
  --ks-key-alias shinecaniep \
  --ks-pass pass:shinecaniep \
  --key-pass pass:shinecaniep \
  <aligned.apk>

# 验证
apksigner verify --print-certs <signed.apk>
```

签名文件信息：

| 项目 | 值 |
|------|-----|
| **文件** | `shinecaniep-release.jks`（项目根目录） |
| **别名** | `shinecaniep` |
| **密码** | `shinecaniep`（keystore 和 key 相同） |
| **公司** | 杭州炫灿科技有限公司 |
| **有效期** | 10,000 天 |
| **算法** | RSA 2048 |

> ⚠️ 签名文件更换后，已安装的旧 APK 需先卸载才能安装新版。

## Android 权限说明

应用在 Android 端需要以下运行时权限：

| 权限 | 用途 | 声明位置 |
|------|------|----------|
| `INTERNET` | 网络访问 | AndroidManifest.xml |
| `CAMERA` | 摄像头（拍照、扫码） | AndroidManifest.xml + 运行时请求 |
| `RECORD_AUDIO` | 麦克风录音 | AndroidManifest.xml + 运行时请求 |
| `BLUETOOTH` / `BLUETOOTH_ADMIN` | 蓝牙（Android 11 及以下） | AndroidManifest.xml |
| `BLUETOOTH_CONNECT` / `BLUETOOTH_SCAN` | 蓝牙（Android 12+） | AndroidManifest.xml + 运行时请求 |
| `ACCESS_FINE_LOCATION` | 蓝牙 LE 扫描定位 | AndroidManifest.xml + 运行时请求 |

权限处理机制：
- `MainActivity.kt` 在 `onCreate()` 中自动请求必要的 Android 运行时权限
- `onWebViewCreate()` 中设置 `WebChromeClient` 桥接 WebView 权限请求到 Android 系统
- 用户首次使用摄像头/蓝牙时会弹出系统授权弹窗

### Windows 快速运行
```bash
.\运行Tauri应用.bat
```

## 安全说明

- Tauri CSP 设置为 `null`（开发环境已禁用）
- 管理员设置：点击右上角热区 3 次 + 输入密码 `299451`
- 应用检测 `file://` 和 `tauri://` 协议，自动适配不同环境

## 许可证

MIT License

## 更新日志

### 2026-06-12
- 品牌更名至"资源教室管理系统-IEP"，包名改为 `com.hzxckj.shinecan.iep`
- 版本升级至 1.0.3
- 新增 `build_apk_cli.py` 命令行打包工具（WSL/Linux 下推荐使用）
- 修复 `build_apk_gui.py` 跨平台兼容性（apksigner 路径、ANDROID_HOME 回退）
- Android Gradle 配置阿里云镜像，无需代理即可构建
- 更新应用图标为 ieplogo

### 2026-06-08
- 添加 Android APK 构建支持（Tauri v2 Android）
- 修复 Android 平板摄像头/蓝牙权限问题：AndroidManifest.xml 添加权限声明，MainActivity.kt 处理 WebView 运行时权限请求
- 新增 `generate_android_icons.py` 图标生成脚本，支持交互式指定源图标和输出目录
- 生成所有密度的 Android mipmap 图标（替换默认 Android 机器人图标）
- 平板视口适配：1280px 桌面视口 + 用户缩放
- 签名密钥库：`shinecaniep-release.jks`（杭州炫灿科技有限公司）

### 2026-04-25
- 新增 `build.js` 打包前置配置脚本，系统名称一键同步到 `dist/config.json`、`dist/index.html`、`src-tauri/Cargo.toml`，支持 Windows 和 Linux
- 清理代码中的调试日志（`console.log`），保留必要的错误日志（`console.error`）

### 2026-04-15
- 移除 iframe，登录表单直接 POST 到服务器
- Rust 端 `WebviewWindowBuilder` 程序化创建窗口
- `on_page_load` 注入导航栏和 F12 开发者工具
- 配置文件改为 exe 同目录读写（`read_config` / `write_config`）

### 2025-03-26
- 新增右下角悬浮导航栏（返回、前进、刷新按钮）
- 登录后隐藏登录界面，导航至外部网页
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
