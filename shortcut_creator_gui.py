#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快捷方式创建工具 - GUI 版本
支持 Windows/macOS/Linux 跨平台创建桌面快捷方式
"""

import json
import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


def get_script_dir() -> Path:
    """获取脚本所在目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.resolve()


def load_config(config_path: Path) -> dict:
    """加载配置文件"""
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_path: Path, config: dict):
    """保存配置文件"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


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


def scan_icons(script_dir: Path) -> list:
    """扫描脚本目录下的图标文件"""
    icon_dirs = [script_dir, script_dir / "src", script_dir / "icons", script_dir / "images"]
    icon_extensions = {".ico", ".icns", ".png", ".svg"}
    icons = []
    
    for icon_dir in icon_dirs:
        if icon_dir.exists():
            for file in icon_dir.iterdir():
                if file.suffix.lower() in icon_extensions:
                    rel_path = str(file.relative_to(script_dir))
                    icons.append({"name": file.name, "path": rel_path, "full_path": str(file)})
    
    return icons


def load_icon_preview(icon_path: str, size: int = 48):
    """加载图标预览图片"""
    try:
        from PIL import Image, ImageTk
        
        if not os.path.exists(icon_path):
            return None
        
        img = Image.open(icon_path)
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except ImportError:
        return None
    except Exception:
        return None


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
        bat_path = output_path.with_suffix('.bat')
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f'@echo off\nstart "" "{target}" {args}\n')
        messagebox.showinfo("提示", f"未安装 pywin32，已创建批处理文件：{bat_path}")
        return True
    except Exception as e:
        messagebox.showerror("错误", f"创建快捷方式失败：{e}")
        return False


def create_shortcut_macos(name: str, target: str, args: str, icon: str, output_path: Path) -> bool:
    """macOS 平台创建快捷方式"""
    try:
        app_name = f"{name}.app"
        app_path = output_path / app_name
        contents_dir = app_path / "Contents"
        contents_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        launch_script = f"""#!/bin/bash
open "{target}" --args {args}
"""
        with open(contents_dir / "MacOS/launch.sh", 'w', encoding='utf-8') as f:
            f.write(launch_script)
        os.chmod(contents_dir / "MacOS/launch.sh", 0o755)
        
        return True
    except Exception as e:
        messagebox.showerror("错误", f"创建快捷方式失败：{e}")
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
        messagebox.showerror("错误", f"创建快捷方式失败：{e}")
        return False


class ShortcutCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("快捷方式创建工具")
        self.root.resizable(False, False)
        
        self.script_dir = get_script_dir()
        self.config_path = self.script_dir / "shortcut-config.json"
        self.config = load_config(self.config_path)
        
        self.browsers = detect_browsers()
        self.icons = scan_icons(self.script_dir)
        
        self.icon_preview_label = None
        self.icon_images = {}
        
        self.create_widgets()
        self.load_config_to_ui()
        
        center_window(root, 550, 500)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        row = 0
        
        ttk.Label(main_frame, text="快捷方式名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.shortcut_name_var = tk.StringVar()
        self.shortcut_name_entry = ttk.Entry(main_frame, textvariable=self.shortcut_name_var, width=45)
        self.shortcut_name_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        ttk.Label(main_frame, text="目标页面:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.target_page_var = tk.StringVar()
        self.target_page_entry = ttk.Entry(main_frame, textvariable=self.target_page_var, width=45)
        self.target_page_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1
        
        ttk.Label(main_frame, text="浏览器:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.browser_var = tk.StringVar()
        self.browser_combo = ttk.Combobox(main_frame, textvariable=self.browser_var, width=42, state="readonly")
        self.browser_combo.grid(row=row, column=1, pady=5, padx=(10, 0))
        
        browser_names = [b["name"] for b in self.browsers] if self.browsers else ["未检测到浏览器"]
        self.browser_combo['values'] = browser_names
        if browser_names:
            self.browser_combo.current(0)
        row += 1
        
        ttk.Label(main_frame, text="图标选择:").grid(row=row, column=0, sticky=tk.W, pady=5)
        
        icon_select_frame = ttk.Frame(main_frame)
        icon_select_frame.grid(row=row, column=1, pady=5, padx=(10, 0), sticky=(tk.W, tk.E))
        
        self.icon_var = tk.StringVar()
        self.icon_combo = ttk.Combobox(icon_select_frame, textvariable=self.icon_var, width=35, state="readonly")
        self.icon_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        icon_names = [icon["name"] for icon in self.icons] if self.icons else ["未找到图标"]
        self.icon_combo['values'] = icon_names
        if icon_names:
            self.icon_combo.current(0)
        self.icon_combo.bind("<<ComboboxSelected>>", self.on_icon_selected)
        
        ttk.Button(icon_select_frame, text="浏览...", command=self.browse_icon).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        ttk.Label(preview_frame, text="图标预览:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, width=54, height=54, bg="#f0f0f0", highlightthickness=1)
        self.preview_canvas.pack(side=tk.LEFT)
        self.preview_canvas.create_text(27, 27, text="无预览", font=("Arial", 8), fill="#999999")
        
        row += 1
        
        self.start_maximized_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="启动时最大化窗口", 
                       variable=self.start_maximized_var).grid(row=row, column=0, columnspan=2, 
                                                               sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(main_frame, text="输出位置:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value="desktop")
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        ttk.Radiobutton(output_frame, text="桌面", variable=self.output_dir_var, 
                       value="desktop").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(output_frame, text="脚本目录", variable=self.output_dir_var, 
                       value="script").pack(side=tk.LEFT)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="创建快捷方式", command=self.create_shortcut).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="green")
        self.status_label.grid(row=row + 1, column=0, columnspan=2, pady=10)
    
    def load_config_to_ui(self):
        self.shortcut_name_var.set(self.config.get("shortcut_name", "资源教室管理系统-IEP"))
        self.target_page_var.set(self.config.get("target_page", "index.html"))
        self.start_maximized_var.set(self.config.get("start_maximized", True))
        self.output_dir_var.set(self.config.get("output_dir", "desktop"))
        
        default_icon = self.config.get("custom_icon", "src/icon.ico")
        if self.icons:
            for i, icon in enumerate(self.icons):
                if icon["path"] == default_icon or icon["name"] == default_icon:
                    self.icon_combo.current(i)
                    self.icon_var.set(default_icon)
                    self.update_icon_preview(default_icon)
                    break
            else:
                self.icon_combo.current(0)
                self.icon_var.set(self.icons[0]["path"])
                self.update_icon_preview(self.icons[0]["path"])
        else:
            self.icon_var.set(default_icon)
        
        default_browser = self.config.get("default_browser_name", "")
        if default_browser and default_browser in self.browser_combo['values']:
            self.browser_combo.set(default_browser)
        elif self.browsers:
            self.browser_combo.set(self.browsers[0]["name"])
    
    def on_icon_selected(self, event=None):
        """图标选择事件处理"""
        selected_index = self.icon_combo.current()
        if selected_index >= 0 and selected_index < len(self.icons):
            icon_path = self.icons[selected_index]["path"]
            self.icon_var.set(icon_path)
            self.update_icon_preview(icon_path)
    
    def update_icon_preview(self, icon_rel_path: str):
        """更新图标预览"""
        icon_full_path = self.script_dir / icon_rel_path
        
        if not icon_full_path.exists():
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(27, 27, text="文件不存在", font=("Arial", 8), fill="#999999")
            return
        
        photo = load_icon_preview(str(icon_full_path))
        if photo:
            self.preview_canvas.delete("all")
            self.icon_images[icon_rel_path] = photo
            self.preview_canvas.create_image(27, 27, image=photo)
        else:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(27, 27, text="无法预览", font=("Arial", 8), fill="#999999")
    
    def get_selected_browser_path(self) -> str:
        selected_name = self.browser_var.get()
        for browser in self.browsers:
            if browser["name"] == selected_name:
                return browser["path"]
        return self.config.get("default_browser", "")
    
    def browse_icon(self):
        file_path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico;*.icns;*.png"), ("所有文件", "*.*")]
        )
        if file_path:
            rel_path = os.path.relpath(file_path, self.script_dir)
            self.icon_var.set(rel_path)
            self.update_icon_preview(rel_path)
    
    def create_shortcut(self):
        shortcut_name = self.shortcut_name_var.get().strip()
        if not shortcut_name:
            messagebox.showwarning("警告", "请输入快捷方式名称")
            return
        
        target_page = self.target_page_var.get().strip()
        if not target_page:
            messagebox.showwarning("警告", "请输入目标页面")
            return
        
        browser_path = self.get_selected_browser_path()
        if not browser_path:
            messagebox.showwarning("警告", "请选择浏览器")
            return
        
        custom_icon = self.icon_var.get().strip()
        icon_path = self.script_dir / custom_icon
        icon_str = str(icon_path) if icon_path.exists() else ""
        
        target_html = self.script_dir / target_page
        
        args = f'"{target_html}"'
        if self.start_maximized_var.get() and platform.system() == "Windows":
            args += " --start-maximized"
        
        if self.output_dir_var.get() == "desktop":
            output_path = get_desktop_path()
        else:
            output_path = self.script_dir
        
        system = platform.system()
        success = False
        
        if system == "Windows":
            success = create_shortcut_windows(
                shortcut_name, browser_path, args, icon_str, output_path
            )
        elif system == "Darwin":
            success = create_shortcut_macos(
                shortcut_name, browser_path, args, icon_str, output_path
            )
        elif system == "Linux":
            success = create_shortcut_linux(
                shortcut_name, browser_path, args, icon_str, output_path
            )
        
        if success:
            self.status_var.set("快捷方式创建成功！")
            messagebox.showinfo("成功", f"快捷方式已创建到：\n{output_path}")
        else:
            self.status_var.set("创建失败")
    
    def save_config(self):
        self.config["shortcut_name"] = self.shortcut_name_var.get().strip()
        self.config["target_page"] = self.target_page_var.get().strip()
        self.config["default_browser_name"] = self.browser_var.get()
        self.config["default_browser"] = self.get_selected_browser_path()
        self.config["custom_icon"] = self.icon_var.get().strip()
        self.config["start_maximized"] = self.start_maximized_var.get()
        self.config["output_dir"] = self.output_dir_var.get()
        
        save_config(self.config_path, self.config)
        self.status_var.set("配置已保存")
        messagebox.showinfo("成功", "配置已保存到 shortcut-config.json")


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def main():
    root = tk.Tk()
    
    try:
        root.tk.call('tk', 'scaling', 2.0)
    except Exception:
        pass
    
    app = ShortcutCreatorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
