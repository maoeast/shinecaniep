# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

送教上门AI成长智联推进系统 (Resource Room Management System - IEP) is a Tauri v2 desktop and Android tablet application with a web frontend. Developed by 杭州炫灿科技有限公司.

## Architecture

### Frontend
- **Single Page Application**: `dist/index.html` contains the complete UI
- **Styling**: Tailwind CSS (from `src/css/tailwind.min.css`) + Font Awesome 6 (`src/css/all.min.css`)
- **Tauri API Module**: `src/js/tauri-api.js` provides JavaScript bindings to Rust backend commands

### Backend (Tauri/Rust)
- **Location**: `src-tauri/src/main.rs` (desktop) + `src-tauri/src/lib.rs` (shared + Android entry point)
- **Version**: Tauri v2
- **Plugins**: shell, dialog, fs
- **Custom Commands**:
  - `read_config` / `write_config` - App config management
  - `get_app_dir` - Get app data directory
  - `select_file_dialog` / `select_save_dialog` - Native file dialogs
  - `file_exists` / `read_file` / `write_file` - File operations
  - `get_system_info` - OS/arch info
  - `execute_command` - Run external commands
  - `create_shortcut` - Cross-platform shortcut creation

## Common Commands

### Tauri Development
```bash
# Development mode (requires Python HTTP server running)
cd src-tauri && cargo tauri dev

# Build desktop release
cd src-tauri && cargo tauri build

# Build Android APK
cd src-tauri && cargo tauri android build

# On Windows, run the built executable
.\运行Tauri应用.bat
```

## File Structure

```
shinecaniep/
├── dist/
│   ├── index.html          # Main SPA frontend (edit here)
│   └── config.json         # App default config
├── src/                    # Static assets
│   ├── css/                # Tailwind + Font Awesome
│   ├── js/tauri-api.js     # Tauri frontend API bindings
│   ├── webfonts/           # Font files
│   └── icon.ico            # App icon
├── src-tauri/              # Tauri/Rust backend
│   ├── Cargo.toml          # Rust dependencies
│   ├── tauri.conf.json     # Tauri configuration
│   ├── src/main.rs         # Desktop entry
│   ├── src/lib.rs          # Shared logic + Android entry point
│   ├── gen/android/        # Android project (auto-generated)
│   ├── icons/              # App icons (multiple formats)
│   └── target/             # Build output
├── shinecaniep-release.jks # Android signing keystore
└── index.html              # Synced copy of dist/index.html
```

## Key Configuration Files

### tauri.conf.json
- Window size: 1400x800 (min: 1024x768)
- Dev server: `http://localhost:1420`
- Frontend dist: `../dist`
- Before dev command: `python -m http.server 1420 --directory ./dist`
- Android minSdk: 24

## Tauri API Usage

The frontend detects Tauri environment and uses `window.__TAURI__.core.invoke()` to call Rust commands:

```javascript
// Example: Read config
const config = await window.__TAURI__.core.invoke('read_config');

// Example: Create shortcut
await window.__TAURI__.core.invoke('create_shortcut', {
    name: 'My Shortcut',
    target: '/path/to/app',
    outputDir: '/home/user/Desktop'
});
```

See `src/js/tauri-api.js` for the complete API wrapper.

## Android APK Build

### Prerequisites
- Android SDK + NDK 28.x
- Rust Android targets: `aarch64-linux-android`, `armv7-linux-androideabi`, `i686-linux-android`, `x86_64-linux-android`

### Signing
- **Keystore**: `shinecaniep-release.jks` (project root)
- **Alias**: `shinecaniep`
- **Password**: `shinecaniep`
- **Company**: 杭州炫灿科技有限公司

### Viewport
- Android uses fixed viewport `width=1280` for tablet compatibility
- Supports pinch-to-zoom

### Build Tips
- After modifying `dist/` files, run `touch src/main.rs` to force recompile
- The unsigned APK needs to be zipaligned and signed manually with `apksigner`

## Build Notes

- Changing `dist/index.html` requires syncing to root `index.html`
- Changing dist files requires `touch src/main.rs` + rebuild (Tauri build script doesn't auto-detect dist changes)
- `config.json` must exist in dist/ directory to be embedded

## Security Notes

- Tauri CSP is set to `null` (disabled) for development
- Admin access to settings requires clicking the top-right hotspot 3 times and entering password `299451`
- Application detects `file://` protocol and `tauri://` protocol for environment-specific behavior
