#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快捷方式创建工具
支持 Windows/macOS/Linux 跨平台创建桌面快捷方式
"""

import json
import os
import sys
import platform
import subprocess
from pathlib import Path


def get_script_dir() -> Path:
    """获取脚本所在目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.resolve()


def load_config(config_path: Path) -> dict:
    """加载配置文件"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_browsers() -> list:
    """自动检测系统已安装的浏览器"""
    system = platform.system()
    browsers = []
    
    if system == "Windows":
        browser_paths = [
            ("360 安全浏览器", r"C:\Users\Administrator\AppData\Roaming\360se6\Application\360se.exe"),
            ("360 极速浏览器", r"C:\Users\Administrator\AppData\Roaming\360Chrome\Chrome\Application\360chrome.exe"),
            ("Google Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ("Google Chrome (x86)", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            ("Microsoft Edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            ("Microsoft Edge (x86)", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            ("Firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
            ("Firefox (x86)", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
        ]
        for name, path in browser_paths:
            if os.path.exists(path):
                browsers.append({"name": name, "path": path})
    
    elif system == "Darwin":
        browser_paths = [
            ("Safari", "/Applications/Safari.app"),
            ("Google Chrome", "/Applications/Google Chrome.app"),
            ("Firefox", "/Applications/Firefox.app"),
            ("Microsoft Edge", "/Applications/Microsoft Edge.app"),
            ("360 安全浏览器", "/Applications/360 安全浏览器.app"),
        ]
        for name, path in browser_paths:
            if os.path.exists(path):
                browsers.append({"name": name, "path": path})
    
    elif system == "Linux":
        browser_commands = {
            "Google Chrome": "google-chrome",
            "Chromium": "chromium-browser",
            "Firefox": "firefox",
            "Microsoft Edge": "microsoft-edge",
            "sensible-browser": "sensible-browser",
        }
        for name, cmd in browser_commands.items():
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    browsers.append({"name": name, "path": result.stdout.strip()})
            except Exception:
                pass
    
    return browsers


def select_browser(browsers: list, default_browser: str = None) -> dict | None:
    """让用户选择浏览器"""
    if not browsers:
        return None
    
    if default_browser:
        for browser in browsers:
            if browser["name"] == default_browser:
                print(f"使用默认浏览器：{browser['name']}")
                return browser
    
    if len(browsers) == 1:
        return browsers[0]
    
    print("\n检测到以下浏览器：")
    for i, browser in enumerate(browsers, 1):
        print(f"  {i}. {browser['name']} ({browser['path']})")
    
    while True:
        try:
            choice = input(f"\n请选择浏览器 (1-{len(browsers)}) [默认: 1]: ").strip()
            if not choice:
                choice = "1"
            idx = int(choice) - 1
            if 0 <= idx < len(browsers):
                return browsers[idx]
            print("无效的选择，请重新输入")
        except ValueError:
            print("请输入数字")


def create_shortcut_windows(name: str, target: str, args: str, icon: str, output_path: Path) -> bool:
    """Windows 平台创建快捷方式"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(output_path))
        shortcut.TargetPath = target
        shortcut.Arguments = args
        shortcut.WorkingDirectory = str(get_script_dir())
        if icon and os.path.exists(icon):
            shortcut.IconLocation = icon
        shortcut.save()
        return True
    except ImportError:
        # 如果没有 pywin32，创建批处理文件作为备用方案
        bat_path = output_path.with_suffix('.bat')
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f'@echo off\nstart "" "{target}" {args}\n')
        print(f"提示：未安装 pywin32，已创建批处理文件：{bat_path}")
        return True
    except Exception as e:
        print(f"创建快捷方式失败：{e}")
        return False


def create_shortcut_macos(name: str, target: str, args: str, icon: str, output_path: Path) -> bool:
    """macOS 平台创建快捷方式"""
    try:
        # 创建一个.app 应用包
        app_name = f"{name}.app"
        app_path = output_path / app_name
        contents_dir = app_path / "Contents"
        contents_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch.sh</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleName</key>
    <string>{name}</string>
</dict>
</plist>"""
        with open(contents_dir / "Info.plist", 'w', encoding='utf-8') as f:
            f.write(info_plist)
        
        # 创建启动脚本
        launch_script = f"""#!/bin/bash
open "{target}" --args {args}
"""
        with open(contents_dir / "MacOS/launch.sh", 'w', encoding='utf-8') as f:
            f.write(launch_script)
        os.chmod(contents_dir / "MacOS/launch.sh", 0o755)
        
        return True
    except Exception as e:
        print(f"创建快捷方式失败：{e}")
        return False


def create_shortcut_linux(name: str, target: str, args: str, icon: str, output_path: Path) -> bool:
    """Linux 平台创建快捷方式"""
    try:
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name}
Exec={target} {args}
Icon={icon if icon and os.path.exists(icon) else 'web-browser'}
Terminal=false
Categories=Application;
"""
        desktop_path = output_path / f"{name}.desktop"
        with open(desktop_path, 'w', encoding='utf-8') as f:
            f.write(desktop_content)
        os.chmod(desktop_path, 0o755)
        return True
    except Exception as e:
        print(f"创建快捷方式失败：{e}")
        return False


def get_desktop_path() -> Path:
    """获取桌面路径"""
    system = platform.system()
    
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
            desktop = winreg.QueryValueEx(key, "Desktop")[0]
            winreg.CloseKey(key)
            return Path(desktop)
        except Exception:
            return Path.home() / "Desktop"
    elif system == "Darwin":
        return Path.home() / "Desktop"
    elif system == "Linux":
        # 尝试获取 XDG 桌面路径
        try:
            result = subprocess.run(
                ["xdg-user-dir", "DESKTOP"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except Exception:
            pass
        return Path.home() / "Desktop"
    
    return Path.home() / "Desktop"


def main():
    """主函数"""
    script_dir = get_script_dir()
    config_path = script_dir / "shortcut-config.json"
    
    print("=" * 50)
    print("快捷方式创建工具")
    print("=" * 50)
    print(f"系统：{platform.system()} {platform.release()}")
    print(f"脚本目录：{script_dir}")
    
    # 加载配置
    try:
        config = load_config(config_path)
        print(f"配置文件：{config_path}")
    except FileNotFoundError as e:
        print(f"错误：{e}")
        print("请确保 config.json 文件存在于脚本目录中")
        return 1
    except json.JSONDecodeError as e:
        print(f"配置文件解析失败：{e}")
        return 1
    
    # 检测浏览器
    print("\n正在检测已安装的浏览器...")
    browsers = detect_browsers()
    
    if not browsers:
        print("未检测到任何浏览器")
        # 使用配置中的默认路径
        default_browser = config.get("default_browser", "")
        if default_browser and os.path.exists(default_browser):
            browsers = [{"name": "自定义浏览器", "path": default_browser}]
        else:
            print("请在配置文件中指定浏览器路径")
            return 1
    
    # 选择浏览器
    default_browser_name = config.get("default_browser_name", "")
    selected_browser = select_browser(browsers, default_browser_name)
    
    if not selected_browser:
        print("未选择浏览器，退出")
        return 1
    
    # 获取配置
    shortcut_name = config.get("shortcut_name", "勤源科技工业系统-IEP")
    target_page = config.get("target_page", "index.html")
    start_maximized = config.get("start_maximized", True)
    custom_icon = config.get("custom_icon", "icon.ico")
    output_dir = config.get("output_dir", "desktop")
    
    # 构建参数
    target_html = script_dir / target_page
    if not target_html.exists():
        print(f"警告：目标文件不存在：{target_html}")
    
    args = f'"{target_html}"'
    if start_maximized:
        system = platform.system()
        if system == "Windows":
            args += " --start-maximized"
    
    # 图标路径
    icon_path = script_dir / custom_icon
    icon_str = str(icon_path) if icon_path.exists() else ""
    if not icon_str:
        print("未找到自定义图标，使用默认图标")
    
    # 输出路径
    if output_dir == "desktop":
        output_path = get_desktop_path()
    elif output_dir == "script":
        output_path = script_dir
    else:
        output_path = Path(output_dir)
    
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    # 创建快捷方式
    print(f"\n创建快捷方式：{shortcut_name}")
    print(f"目标浏览器：{selected_browser['name']}")
    print(f"目标文件：{target_html}")
    print(f"输出位置：{output_path}")
    
    system = platform.system()
    if system == "Windows":
        success = create_shortcut_windows(
            shortcut_name,
            selected_browser['path'],
            args,
            icon_str,
            output_path
        )
    elif system == "Darwin":
        success = create_shortcut_macos(
            shortcut_name,
            selected_browser['path'],
            args,
            icon_str,
            output_path
        )
    elif system == "Linux":
        success = create_shortcut_linux(
            shortcut_name,
            selected_browser['path'],
            args,
            icon_str,
            output_path
        )
    else:
        print(f"不支持的操作系统：{system}")
        return 1
    
    if success:
        print("\n快捷方式创建成功！")
        return 0
    else:
        print("\n快捷方式创建失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
