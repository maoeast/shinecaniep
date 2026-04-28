// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::{Path, PathBuf};
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_dialog::DialogExt;

/// 应用配置结构体（通用 JSON，不限定字段）
pub type AppConfig = serde_json::Value;

const BUILTIN_SHORTCUT_ICONS: &[(&str, &[u8])] = &[
    ("AI.ico", include_bytes!("../../dist/src/icon/AI.ico")),
    ("app.ico", include_bytes!("../../dist/src/icon/app.ico")),
    ("app2.ico", include_bytes!("../../dist/src/icon/app2.ico")),
    ("app4.ico", include_bytes!("../../dist/src/icon/app4.ico")),
    ("book.ico", include_bytes!("../../dist/src/icon/book.ico")),
    ("icon.ico", include_bytes!("../../dist/src/icon/icon.ico")),
    ("math.ico", include_bytes!("../../dist/src/icon/math.ico")),
    ("xqkf.ico", include_bytes!("../../dist/src/icon/xqkf.ico")),
];

fn ensure_builtin_shortcut_icons(icon_dir: &Path) -> Result<(), String> {
    if !icon_dir.exists() {
        std::fs::create_dir_all(icon_dir)
            .map_err(|e| format!("创建内置图标目录失败: {}", e))?;
    }

    for (name, data) in BUILTIN_SHORTCUT_ICONS {
        let icon_path = icon_dir.join(name);
        if icon_path.exists() {
            continue;
        }

        std::fs::write(&icon_path, data)
            .map_err(|e| format!("写入内置图标失败 ({}): {}", name, e))?;
    }

    Ok(())
}

/// 获取 exe 所在目录的 config.json 路径
fn get_config_path() -> Result<PathBuf, String> {
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("无法获取 exe 路径: {}", e))?;
    let exe_dir = exe_path.parent()
        .ok_or("无法获取 exe 所在目录")?;
    Ok(exe_dir.join("config.json"))
}

/// 获取 exe 所在目录
#[tauri::command]
fn get_app_dir() -> Result<String, String> {
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("无法获取 exe 路径: {}", e))?;
    let exe_dir = exe_path.parent()
        .ok_or("无法获取 exe 所在目录")?;
    Ok(exe_dir.to_string_lossy().to_string())
}

/// 获取 exe 完整路径
#[tauri::command]
fn get_exe_path() -> Result<String, String> {
    let exe_path = std::env::current_exe()
        .map_err(|e| format!("无法获取 exe 路径: {}", e))?;
    Ok(exe_path.to_string_lossy().to_string())
}

/// 读取配置文件（exe 同目录下的 config.json）
#[tauri::command]
fn read_config() -> Result<serde_json::Value, String> {
    let config_path = get_config_path()?;

    if !config_path.exists() {
        return Ok(serde_json::Value::Null);
    }

    let content = std::fs::read_to_string(&config_path)
        .map_err(|e| format!("读取配置文件失败: {}", e))?;

    let config: serde_json::Value = serde_json::from_str(&content)
        .map_err(|e| format!("解析配置文件失败: {}", e))?;

    Ok(config)
}

/// 写入配置文件（exe 同目录下的 config.json）
#[tauri::command]
fn write_config(config: serde_json::Value) -> Result<(), String> {
    let config_path = get_config_path()?;

    let content = serde_json::to_string_pretty(&config)
        .map_err(|e| format!("序列化配置失败: {}", e))?;

    std::fs::write(&config_path, content)
        .map_err(|e| format!("写入配置文件失败: {}", e))?;

    Ok(())
}

/// 选择文件对话框
#[tauri::command]
async fn select_file_dialog(
    app: tauri::AppHandle,
    _window: tauri::Window,
    title: String,
    filters: Option<Vec<(String, Vec<String>)>>,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let mut dialog = app
        .dialog()
        .file()
        .set_title(&title);

    if let Some(filters) = filters {
        for (name, extensions) in filters {
            let extensions: Vec<&str> = extensions.iter().map(String::as_str).collect();
            dialog = dialog.add_filter(&name, &extensions);
        }
    }

    let file_path = dialog.blocking_pick_file();

    Ok(file_path.map(|p| p.to_string()))
}

/// 选择保存文件对话框
#[tauri::command]
async fn select_save_dialog(
    app: tauri::AppHandle,
    _window: tauri::Window,
    title: String,
    default_name: String,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let file_path = app
        .dialog()
        .file()
        .set_title(&title)
        .set_file_name(&default_name)
        .blocking_save_file();

    Ok(file_path.map(|p| p.to_string()))
}

/// 执行外部命令（用于调用 Python 脚本）
#[tauri::command]
async fn execute_command(command: String, args: Vec<String>) -> Result<String, String> {
    use std::process::Command;

    let output = Command::new(&command)
        .args(&args)
        .output()
        .map_err(|e| format!("执行命令失败: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        return Err(format!("命令执行出错: {}", stderr));
    }

    Ok(stdout)
}

/// 检查文件是否存在
#[tauri::command]
fn file_exists(path: String) -> bool {
    std::path::Path::new(&path).exists()
}

/// 读取文件内容为文本
#[tauri::command]
fn read_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path)
        .map_err(|e| format!("读取文件失败: {}", e))
}

/// 写入文件内容
#[tauri::command]
fn write_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, content)
        .map_err(|e| format!("写入文件失败: {}", e))
}

/// 获取桌面路径
#[tauri::command]
async fn get_desktop_path() -> Result<String, String> {
    use std::process::Command;

    let output = Command::new("powershell")
        .args(&["-Command", "[Environment]::GetFolderPath('Desktop')"])
        .output()
        .map_err(|e| format!("获取桌面路径失败: {}", e))?;

    if !output.status.success() {
        return Err(format!(
            "获取桌面路径失败: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok(path)
}

/// 获取系统信息
#[tauri::command]
fn get_system_info() -> serde_json::Value {
    use std::env;

    serde_json::json!({
        "os": env::consts::OS,
        "arch": env::consts::ARCH,
        "family": env::consts::FAMILY,
    })
}

/// 创建快捷方式（跨平台）
#[tauri::command]
async fn create_shortcut(
    _app: tauri::AppHandle,
    name: String,
    target: String,
    icon_path: Option<String>,
    output_dir: String,
) -> Result<String, String> {
    let os = std::env::consts::OS;

    match os {
        "windows" => create_windows_shortcut(&name, &target, icon_path.as_deref(), &output_dir),
        "macos" => create_macos_shortcut(&name, &target, icon_path.as_deref(), &output_dir),
        "linux" => create_linux_shortcut(&name, &target, icon_path.as_deref(), &output_dir),
        _ => Err(format!("不支持的操作系统: {}", os)),
    }
}

/// 创建 Windows 快捷方式
fn create_windows_shortcut(
    name: &str,
    target: &str,
    icon_path: Option<&str>,
    output_dir: &str,
) -> Result<String, String> {
    use std::process::Command;

    // 使用 PowerShell 创建快捷方式
    let shortcut_path = format!("{}\\{}.lnk", output_dir, name);

    let icon_line = icon_path
        .map(|p| format!(r#"$Shortcut.IconLocation = "{}""#, p))
        .unwrap_or_default();

    let ps_script = format!(
        r#"
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{}")
        $Shortcut.TargetPath = "{}"
        {}
        $Shortcut.Save()
        "#,
        shortcut_path, target, icon_line
    );

    let output = Command::new("powershell")
        .args(&["-Command", &ps_script])
        .output()
        .map_err(|e| format!("创建快捷方式失败: {}", e))?;

    if !output.status.success() {
        return Err(format!(
            "创建快捷方式失败: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    Ok(shortcut_path)
}

/// 创建 macOS 快捷方式 (.app 包)
fn create_macos_shortcut(
    name: &str,
    target: &str,
    icon_path: Option<&str>,
    output_dir: &str,
) -> Result<String, String> {
    let app_path = format!("{}/{}.app", output_dir, name);
    let contents_path = format!("{}/Contents", app_path);
    let macos_path = format!("{}/MacOS", contents_path);

    // 创建目录结构
    std::fs::create_dir_all(&macos_path)
        .map_err(|e| format!("创建应用目录失败: {}", e))?;

    // 创建启动脚本
    let script_content = format!(
        r#"#!/bin/bash
open "{}"
"#,
        target
    );

    let script_path = format!("{}/{}", macos_path, name);
    std::fs::write(&script_path, script_content)
        .map_err(|e| format!("写入启动脚本失败: {}", e))?;

    // 设置执行权限
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&script_path)
            .map_err(|e| format!("获取文件权限失败: {}", e))?
            .permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&script_path, perms)
            .map_err(|e| format!("设置文件权限失败: {}", e))?;
    }

    // 创建 Info.plist
    let plist_content = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{}</string>
    <key>CFBundleIdentifier</key>
    <string>com.shinecaniep.{}</string>
    <key>CFBundleName</key>
    <string>{}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
</dict>
</plist>"#,
        name, name.to_lowercase().replace(" ", "-"), name
    );

    std::fs::write(format!("{}/Info.plist", contents_path), plist_content)
        .map_err(|e| format!("写入 Info.plist 失败: {}", e))?;

    // 复制图标（如果提供）
    if let Some(icon) = icon_path {
        let icon_dest = format!("{}/AppIcon.icns", contents_path);
        std::fs::copy(icon, &icon_dest)
            .map_err(|e| format!("复制图标失败: {}", e))?;
    }

    Ok(app_path)
}

/// 创建 Linux 快捷方式 (.desktop 文件)
fn create_linux_shortcut(
    name: &str,
    target: &str,
    icon_path: Option<&str>,
    output_dir: &str,
) -> Result<String, String> {
    let desktop_path = format!("{}/{}.desktop", output_dir, name.to_lowercase().replace(" ", "-"));

    let icon_param = icon_path.map(|p| format!("Icon={}\n", p)).unwrap_or_default();

    let desktop_content = format!(
        r#"[Desktop Entry]
Name={}
Exec={}
Type=Application
Terminal=false
{}"#,
        name, target, icon_param
    );

    std::fs::write(&desktop_path, desktop_content)
        .map_err(|e| format!("写入 .desktop 文件失败: {}", e))?;

    // 设置执行权限
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&desktop_path)
            .map_err(|e| format!("获取文件权限失败: {}", e))?
            .permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&desktop_path, perms)
            .map_err(|e| format!("设置文件权限失败: {}", e))?;
    }

    Ok(desktop_path)
}

/// WebView 导航命令 - 后退
#[tauri::command]
fn webview_go_back(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.eval("window.history.back();").map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// WebView 导航命令 - 前进
#[tauri::command]
fn webview_go_forward(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.eval("window.history.forward();").map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// WebView 导航命令 - 刷新
#[tauri::command]
fn webview_reload(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.eval("window.location.reload();").map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// 打开/关闭 DevTools
#[tauri::command]
fn toggle_devtools(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        if window.is_devtools_open() {
            window.close_devtools();
        } else {
            window.open_devtools();
        }
    }
    Ok(())
}

/// 注入到服务器页面的导航栏 JS（纯 JS，无外部依赖）
const NAV_BAR_JS: &str = r#"
(function() {
    if (document.getElementById('tauri-nav-bar')) return;

    var nav = document.createElement('div');
    nav.id = 'tauri-nav-bar';
    nav.style.cssText = 'position:fixed;bottom:30px;right:30px;display:flex;gap:12px;z-index:2147483647;padding:10px 16px;background:rgba(255,255,255,0.15);backdrop-filter:blur(10px);border-radius:30px;box-shadow:0 4px 20px rgba(0,0,0,0.15);border:1px solid rgba(255,255,255,0.2);opacity:0.4;transform:scale(0.9);transition:all 0.3s ease;';

    var btns = [
        { id:'nav-back', label:'\u25C0', title:'返回', action:'window.history.back()' },
        { id:'nav-forward', label:'\u25B6', title:'前进', action:'window.history.forward()' },
        { id:'nav-refresh', label:'\u21BB', title:'刷新', action:'window.location.reload()' }
    ];

    btns.forEach(function(b) {
        var btn = document.createElement('button');
        btn.id = b.id;
        btn.textContent = b.label;
        btn.title = b.title;
        btn.style.cssText = 'width:40px;height:40px;border-radius:50%;border:none;background:rgba(0,188,212,0.9);color:white;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s ease;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
        btn.onmouseenter = function() { btn.style.transform='scale(1.1)'; btn.style.background='rgba(0,188,212,1)'; };
        btn.onmouseleave = function() { btn.style.transform='scale(1)'; btn.style.background='rgba(0,188,212,0.9)'; };
        btn.onclick = function(e) { e.preventDefault(); e.stopPropagation(); eval(b.action); };
        nav.appendChild(btn);
    });

    nav.onmouseenter = function() { nav.style.opacity='1'; nav.style.transform='scale(1)'; };
    nav.onmouseleave = function() { nav.style.opacity='0.4'; nav.style.transform='scale(0.9)'; };

    document.body.appendChild(nav);
})();
"#;

/// 注入到登录页面的 F12 DevTools 快捷键 JS
const F12_JS: &str = r#"
(function() {
    if (window.__f12_injected) return;
    window.__f12_injected = true;
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F12') {
            e.preventDefault();
            if (window.__TAURI__ && window.__TAURI__.core) {
                window.__TAURI__.core.invoke('toggle_devtools');
            }
        }
    });
})();
"#;

const DIRECT_DOWNLOAD_LINK_JS: &str = r#"
(function() {
    if (window.__direct_download_fix_injected) return;
    window.__direct_download_fix_injected = true;

    document.addEventListener('click', function(event) {
        var el = event.target;
        while (el && el.tagName !== 'A') {
            el = el.parentElement;
        }
        if (!el) return;

        var href = el.getAttribute('href');
        if (!href) return;

        var url;
        try {
            url = new URL(href, window.location.href);
        } catch (_) {
            return;
        }

        var pathname = (url.pathname || '').toLowerCase();
        var isTargetSite = url.hostname === 'xcpm.hzxckj308.com' && (url.port === '8008' || url.port === '');
        var isDownloadLink =
            pathname.indexOf('/filemould/') !== -1 ||
            /\.(doc|docx|xls|xlsx|ppt|pptx|pdf|zip|rar|7z|txt)$/.test(pathname);

        if (isTargetSite && isDownloadLink) {
            el.target = '_self';
            el.removeAttribute('target');
            el.removeAttribute('rel');
        }
    }, true);
})();
"#;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_app_dir,
            get_exe_path,
            read_config,
            write_config,
            select_file_dialog,
            select_save_dialog,
            execute_command,
            file_exists,
            read_file,
            write_file,
            get_system_info,
            create_shortcut,
            get_desktop_path,
            webview_go_back,
            webview_go_forward,
            webview_reload,
            toggle_devtools,
        ])
        .setup(|app| {
            println!("资源教室管理系统-IEP 已启动");

            // 确保应用数据目录存在
            match app.path().app_data_dir() {
                Ok(app_dir) => {
                    if !app_dir.exists() {
                        let _ = std::fs::create_dir_all(&app_dir);
                    }
                    println!("应用数据目录: {:?}", app_dir);
                }
                Err(e) => {
                    println!("无法获取应用数据目录: {}", e);
                }
            }

            // 将 config.json 和 icon 文件夹复制到 exe 旁边（仅首次安装时）
            if let Ok(exe_path) = std::env::current_exe() {
                if let Some(exe_dir) = exe_path.parent() {
                    // config.json
                    let target_config = exe_dir.join("config.json");
                    if !target_config.exists() {
                        let config_content = include_str!("../../dist/config.json");
                        let _ = std::fs::write(&target_config, config_content);
                        println!("[Setup] 已复制 config.json 到 exe 目录");
                    }

                    // icon 文件夹
                    let icon_dir = exe_dir.join("icon");
                    if !icon_dir.exists() {
                        let _ = std::fs::create_dir_all(&icon_dir);
                        let icons: &[(&str, &[u8])] = &[
                            ("AI.ico", include_bytes!("../../dist/src/icon/AI.ico")),
                            ("app.ico", include_bytes!("../../dist/src/icon/app.ico")),
                            ("app2.ico", include_bytes!("../../dist/src/icon/app2.ico")),
                            ("app4.ico", include_bytes!("../../dist/src/icon/app4.ico")),
                            ("book.ico", include_bytes!("../../dist/src/icon/book.ico")),
                            ("icon.ico", include_bytes!("../../dist/src/icon/icon.ico")),
                            ("math.ico", include_bytes!("../../dist/src/icon/math.ico")),
                            ("xqkf.ico", include_bytes!("../../dist/src/icon/xqkf.ico")),
                        ];
                        for (name, data) in icons {
                            let _ = std::fs::write(icon_dir.join(name), data);
                        }
                        println!("[Setup] 已复制 icon 文件夹到 exe 目录");
                    }
                }
            }

            // 程序化创建主窗口
            if let Ok(exe_path) = std::env::current_exe() {
                if let Some(exe_dir) = exe_path.parent() {
                    let icon_dir = exe_dir.join("icon");
                    if let Err(error) = ensure_builtin_shortcut_icons(&icon_dir) {
                        println!("[Setup] 鍚屾鍐呯疆 icon 鏂囦欢澶辫触: {}", error);
                    }
                }
            }

            let url = if cfg!(debug_assertions) {
                WebviewUrl::External("http://localhost:1420".parse().unwrap())
            } else {
                WebviewUrl::App("index.html".into())
            };

            WebviewWindowBuilder::new(app, "main", url)
                .title("ShineCanIEP")
                .inner_size(1400.0, 800.0)
                .min_inner_size(1024.0, 768.0)
                .center()
                .resizable(true)
                .on_download(|webview, event| {
                    match event {
                        tauri::webview::DownloadEvent::Requested { url, destination } => {
                            let is_target_download = url.host_str() == Some("xcpm.hzxckj308.com")
                                && url.path().to_ascii_lowercase().contains("/filemould/");

                            if !is_target_download {
                                return true;
                            }

                            let suggested_name = destination
                                .file_name()
                                .and_then(|name| name.to_str())
                                .filter(|name| !name.is_empty())
                                .map(|name| name.to_string())
                                .or_else(|| {
                                    url.path_segments()
                                        .and_then(|mut segments| segments.next_back())
                                        .filter(|name| !name.is_empty())
                                        .map(|name| name.to_string())
                                })
                                .unwrap_or_else(|| "download".to_string());

                            let mut dialog = rfd::FileDialog::new()
                                .set_title("保存下载文件")
                                .set_file_name(&suggested_name);

                            if let Some(parent) = destination.parent() {
                                dialog = dialog.set_directory(parent);
                            }

                            if let Some(path) = dialog.save_file() {
                                *destination = path;
                                true
                            } else {
                                false
                            }
                        }
                        tauri::webview::DownloadEvent::Finished { url, path, success } => {
                            let is_target_download = url.host_str() == Some("xcpm.hzxckj308.com")
                                && url.path().to_ascii_lowercase().contains("/filemould/");

                            if is_target_download && success {
                                let message = if let Some(path) = path {
                                    format!("文件已下载到:\n{}", path.display())
                                } else {
                                    "文件下载完成。".to_string()
                                };

                                webview
                                    .app_handle()
                                    .dialog()
                                    .message(message)
                                    .title("下载完成")
                                    .show(|_| {});
                            }
                            true
                        }
                        _ => true,
                    }
                })
                .on_page_load(|window, payload| {
                    if payload.event() == tauri::webview::PageLoadEvent::Finished {
                        let url = payload.url();
                        let url_str = url.as_str();
                        println!("[PageLoad] URL: {}", url_str);

                        if url_str.contains("xcpm.hzxckj308.com") {
                            // 服务器页面：注入导航栏
                            let _ = window.eval(NAV_BAR_JS);
                            // 也注入 F12 支持
                            let _ = window.eval(F12_JS);
                            let _ = window.eval(DIRECT_DOWNLOAD_LINK_JS);
                            println!("[PageLoad] Injected nav bar + F12");
                        } else if url_str.starts_with("tauri://") || url_str.starts_with("http://localhost") || url_str.starts_with("https://tauri.") || url_str.contains("index.html") || url_str.starts_with("file://") {
                            // 登录页面：注入 F12 DevTools 支持
                            let _ = window.eval(F12_JS);
                            println!("[PageLoad] Injected F12 on login page");
                        }
                    }
                })
                .build()
                .expect("failed to create main window");

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::{ensure_builtin_shortcut_icons, BUILTIN_SHORTCUT_ICONS};
    use std::{
        path::PathBuf,
        time::{SystemTime, UNIX_EPOCH},
    };

    struct TempDirGuard {
        path: PathBuf,
    }

    impl TempDirGuard {
        fn new(prefix: &str) -> Self {
            let unique = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("system time before unix epoch")
                .as_nanos();
            let path = std::env::temp_dir().join(format!("{}_{}", prefix, unique));
            std::fs::create_dir_all(&path).expect("failed to create temp dir");
            Self { path }
        }
    }

    impl Drop for TempDirGuard {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.path);
        }
    }

    #[test]
    fn ensure_builtin_shortcut_icons_creates_all_icons_in_empty_directory() {
        let temp_dir = TempDirGuard::new("shinecaniep_icons_empty");
        let icon_dir = temp_dir.path.join("icon");

        ensure_builtin_shortcut_icons(&icon_dir).expect("expected builtin icons to be written");

        for (name, bytes) in BUILTIN_SHORTCUT_ICONS {
            let icon_path = icon_dir.join(name);
            assert!(icon_path.exists(), "missing builtin icon: {}", name);
            assert_eq!(
                std::fs::read(&icon_path).expect("failed to read written icon"),
                *bytes,
                "icon contents do not match for {}",
                name
            );
        }
    }

    #[test]
    fn ensure_builtin_shortcut_icons_repairs_missing_files_in_existing_directory() {
        let temp_dir = TempDirGuard::new("shinecaniep_icons_partial");
        let icon_dir = temp_dir.path.join("icon");
        std::fs::create_dir_all(&icon_dir).expect("failed to create partial icon dir");

        let existing_icon_path = icon_dir.join(BUILTIN_SHORTCUT_ICONS[0].0);
        std::fs::write(&existing_icon_path, BUILTIN_SHORTCUT_ICONS[0].1)
            .expect("failed to seed existing icon");

        ensure_builtin_shortcut_icons(&icon_dir).expect("expected missing icons to be restored");

        for (name, _) in BUILTIN_SHORTCUT_ICONS {
            assert!(
                icon_dir.join(name).exists(),
                "missing builtin icon after repair: {}",
                name
            );
        }
    }
}
