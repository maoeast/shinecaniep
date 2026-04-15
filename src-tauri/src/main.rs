// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

/// 应用配置结构体
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub system_name: String,
    pub system_name_en: String,
    pub loading_text: String,
    pub copyright: String,
    pub theme: String,
    pub login_style: String,
    pub bg_opacity: i32,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            system_name: "资源教室管理系统-IEP".to_string(),
            system_name_en: "IEP Resource Room Management System".to_string(),
            loading_text: "系统加载中".to_string(),
            copyright: "杭州炫灿科技有限公司".to_string(),
            theme: "tech".to_string(),
            login_style: "modern".to_string(),
            bg_opacity: 30,
        }
    }
}

/// 获取应用配置目录
#[tauri::command]
fn get_app_dir(app: tauri::AppHandle) -> Result<String, String> {
    let app_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("无法获取应用数据目录: {}", e))?;

    // 确保目录存在
    if !app_dir.exists() {
        std::fs::create_dir_all(&app_dir).map_err(|e| format!("创建目录失败: {}", e))?;
    }

    Ok(app_dir.to_string_lossy().to_string())
}

/// 读取配置文件
#[tauri::command]
fn read_config(app: tauri::AppHandle) -> Result<AppConfig, String> {
    let app_dir = get_app_dir(app)?;
    let config_path = PathBuf::from(&app_dir).join("config.json");

    if !config_path.exists() {
        // 返回默认配置
        return Ok(AppConfig::default());
    }

    let content = std::fs::read_to_string(&config_path)
        .map_err(|e| format!("读取配置文件失败: {}", e))?;

    let config: AppConfig = serde_json::from_str(&content)
        .map_err(|e| format!("解析配置文件失败: {}", e))?;

    Ok(config)
}

/// 写入配置文件
#[tauri::command]
fn write_config(app: tauri::AppHandle, config: AppConfig) -> Result<(), String> {
    let app_dir = get_app_dir(app)?;
    let config_path = PathBuf::from(&app_dir).join("config.json");

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
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;

    let file_path = app
        .dialog()
        .file()
        .set_title(&title)
        .blocking_pick_file();

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

    let icon_param = icon_path.map(|p| format!(", \"{}\"", p)).unwrap_or_default();

    let ps_script = format!(
        r#"
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{}")
        $Shortcut.TargetPath = "{}"{}
        $Shortcut.Save()
        "#,
        shortcut_path, target, icon_param
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

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_app_dir,
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

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
