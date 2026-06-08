# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

资源教室管理系统-IEP (Resource Room Management System - IEP) is a Tauri v2 desktop application with a web frontend.

## Architecture

### Frontend
- **Single Page Application**: `index.html` contains the complete UI
- **Styling**: Tailwind CSS (from `src/css/tailwind.min.css`) + Font Awesome 6 (`src/css/all.min.css`)
- **Tauri API Module**: `src/js/tauri-api.js` provides JavaScript bindings to Rust backend commands

### Backend (Tauri/Rust)
- **Location**: `src-tauri/src/main.rs`
- **Version**: Tauri v2 (2.0.0-rc)
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

# Build release version
cd src-tauri && cargo tauri build

# On Windows, run the built executable
.\运行Tauri应用.bat
```

## File Structure

```
shinecaniep/
├── index.html                 # Main SPA frontend
├── config.json               # Runtime app configuration
├── src/                      # Static assets
│   ├── css/                 # Tailwind + Font Awesome
│   ├── js/tauri-api.js      # Tauri frontend API bindings
│   ├── webfonts/            # Font files
│   └── icon.ico             # App icon
├── src-tauri/               # Tauri/Rust backend
│   ├── Cargo.toml           # Rust dependencies
│   ├── tauri.conf.json      # Tauri configuration
│   ├── src/main.rs          # Rust backend code
│   ├── icons/               # App icons (multiple formats)
│   └── target/              # Build output
└── dist/                    # Build distribution
```

## Key Configuration Files

### tauri.conf.json
- Window size: 1400x800 (min: 1024x768)
- Dev server: `http://localhost:1420`
- Frontend dist: `../dist`
- Before dev command: `python -m http.server 1420 --directory ./dist`

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

## Security Notes

- Tauri CSP is set to `null` (disabled) for development
- Admin access to settings requires clicking the top-right hotspot 3 times and entering password `299451`
- Application detects `file://` protocol and `tauri://` protocol for environment-specific behavior
