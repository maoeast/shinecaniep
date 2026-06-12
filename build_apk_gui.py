#!/usr/bin/env python3
"""
APK 打包 GUI 工具
可视化配置应用信息、生成图标、构建签名 APK

用法: python build_apk_gui.py
"""

import os
import sys
import json
import re
import subprocess
import threading
import base64
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk

# ── 项目路径 ──
ROOT = Path(__file__).parent.resolve()
TAURI_CONF = ROOT / "src-tauri" / "tauri.conf.json"
CARGO_TOML = ROOT / "src-tauri" / "Cargo.toml"
MAIN_RS = ROOT / "src-tauri" / "src" / "main.rs"
DIST_CONFIG = ROOT / "dist" / "config.json"
DIST_INDEX = ROOT / "dist" / "index.html"
ROOT_INDEX = ROOT / "index.html"
STRINGS_XML = ROOT / "src-tauri" / "gen" / "android" / "app" / "src" / "main" / "res" / "values" / "strings.xml"
BUILD_GRADLE = ROOT / "src-tauri" / "gen" / "android" / "app" / "build.gradle.kts"
KEYSTORE = ROOT / "shinecaniep-release.jks"

# Android mipmap sizes
LAUNCHER_SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND_CANVAS = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
ICON_SAFE_RATIO = 0.625


# ══════════════════════════════════════════════════════════════
#  Config readers
# ══════════════════════════════════════════════════════════════

def read_tauri_conf():
    with open(TAURI_CONF, "r", encoding="utf-8") as f:
        return json.load(f)

def read_dist_config():
    with open(DIST_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def read_strings_xml():
    if not STRINGS_XML.exists():
        return {"app_name": "", "main_activity_title": ""}
    with open(STRINGS_XML, "r", encoding="utf-8") as f:
        content = f.read()
    app_name = re.search(r'name="app_name"[^>]*>([^<]+)', content)
    title = re.search(r'name="main_activity_title"[^>]*>([^<]+)', content)
    return {
        "app_name": app_name.group(1) if app_name else "",
        "main_activity_title": title.group(1) if title else "",
    }

def read_application_id():
    if not BUILD_GRADLE.exists():
        return ""
    with open(BUILD_GRADLE, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'applicationId\s*=\s*"([^"]+)"', content)
    return m.group(1) if m else ""


# ══════════════════════════════════════════════════════════════
#  Config writers
# ══════════════════════════════════════════════════════════════

def write_tauri_conf(product_name, version, identifier, copyright_):
    content = TAURI_CONF.read_text(encoding="utf-8")
    content = re.sub(r'"productName"\s*:\s*"[^"]*"', f'"productName": "{product_name}"', content)
    content = re.sub(r'"version"\s*:\s*"[^"]*"', f'"version": "{version}"', content)
    content = re.sub(r'"identifier"\s*:\s*"[^"]*"', f'"identifier": "{identifier}"', content)
    if copyright_:
        content = re.sub(r'"copyright"\s*:\s*"[^"]*"', f'"copyright": "{copyright_}"', content)
    TAURI_CONF.write_text(content, encoding="utf-8")

def write_cargo_toml(name, version):
    content = CARGO_TOML.read_text(encoding="utf-8")
    content = re.sub(r'^name\s*=\s*"[^"]*"', f'name = "{name}"', content, flags=re.MULTILINE)
    content = re.sub(r'^version\s*=\s*"[^"]*"', f'version = "{version}"', content, flags=re.MULTILINE)
    content = re.sub(r'^description\s*=\s*"[^"]*"', f'description = "{name}"', content, flags=re.MULTILINE)
    CARGO_TOML.write_text(content, encoding="utf-8")

def write_main_rs_title(title):
    content = MAIN_RS.read_text(encoding="utf-8")
    content = re.sub(r'\.title\("[^"]*"\)', f'.title("{title}")', content)
    MAIN_RS.write_text(content, encoding="utf-8")

def write_dist_config(system_name, system_name_en, copyright_):
    config = read_dist_config()
    config["systemName"] = system_name
    config["systemNameEn"] = system_name_en
    if copyright_:
        config["copyright"] = copyright_
    DIST_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def write_dist_index_title(title):
    content = DIST_INDEX.read_text(encoding="utf-8")
    content = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", content)
    DIST_INDEX.write_text(content, encoding="utf-8")

def write_strings_xml(app_name):
    if not STRINGS_XML.exists():
        return
    content = STRINGS_XML.read_text(encoding="utf-8")
    content = re.sub(r'(<string name="app_name">)[^<]*(</string>)', rf'\g<1>{app_name}\g<2>', content)
    content = re.sub(r'(<string name="main_activity_title">)[^<]*(</string>)', rf'\g<1>{app_name}\g<2>', content)
    STRINGS_XML.write_text(content, encoding="utf-8")

def write_application_id(app_id):
    if not BUILD_GRADLE.exists():
        return
    content = BUILD_GRADLE.read_text(encoding="utf-8")
    content = re.sub(r'applicationId\s*=\s*"[^"]*"', f'applicationId = "{app_id}"', content)
    BUILD_GRADLE.write_text(content, encoding="utf-8")

def sync_index_html():
    if DIST_INDEX.exists():
        ROOT_INDEX.write_text(DIST_INDEX.read_text(encoding="utf-8"), encoding="utf-8")

def update_logo_in_config(logo_path):
    if not logo_path or not os.path.isfile(logo_path):
        return
    import io
    img = Image.open(logo_path).convert("RGBA")
    max_size = 512
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    config = read_dist_config()
    config["logoUrl"] = b64
    DIST_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


# ══════════════════════════════════════════════════════════════
#  Icon generation
# ══════════════════════════════════════════════════════════════

def generate_android_icons(src_path, res_dir, log_fn=print):
    src = Image.open(src_path).convert("RGBA")
    log_fn(f"Source icon: {src.size[0]}x{src.size[1]}")

    for density, size in LAUNCHER_SIZES.items():
        mipmap_dir = os.path.join(res_dir, f"mipmap-{density}")
        os.makedirs(mipmap_dir, exist_ok=True)
        canvas = FOREGROUND_CANVAS[density]
        icon_inner = int(canvas * ICON_SAFE_RATIO)

        icon = src.resize((size, size), Image.LANCZOS)
        icon.save(os.path.join(mipmap_dir, "ic_launcher.png"))
        log_fn(f"  mipmap-{density}/ic_launcher.png {size}x{size}")

        round_icon = src.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
        round_icon.putalpha(mask)
        round_icon.save(os.path.join(mipmap_dir, "ic_launcher_round.png"))

        icon_fg = src.resize((icon_inner, icon_inner), Image.LANCZOS)
        fg = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        offset = (canvas - icon_inner) // 2
        fg.paste(icon_fg, (offset, offset), icon_fg)
        fg.save(os.path.join(mipmap_dir, "ic_launcher_foreground.png"))

    bg_path = os.path.join(res_dir, "drawable", "ic_launcher_background.xml")
    os.makedirs(os.path.dirname(bg_path), exist_ok=True)
    with open(bg_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
                '    android:width="108dp" android:height="108dp"\n'
                '    android:viewportWidth="108" android:viewportHeight="108">\n'
                '    <path android:fillColor="#00000000" android:pathData="M0,0h108v108h-108z" />\n'
                '</vector>\n')
    log_fn("Done! 16 icon files generated.")


# ══════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════

class BuildGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("APK 打包工具")
        self.root.geometry("720x820")
        self.root.resizable(True, True)
        self.root.minsize(600, 700)

        self.var_app_name = tk.StringVar()
        self.var_package = tk.StringVar()
        self.var_version = tk.StringVar()
        self.var_company = tk.StringVar()
        self.var_icon_path = tk.StringVar()

        self.var_cn_name = tk.StringVar()
        self.var_en_name = tk.StringVar()
        self.var_page_version = tk.StringVar()
        self.var_page_company = tk.StringVar()
        self.var_logo_path = tk.StringVar()

        self.icon_preview_img = None
        self.logo_preview_img = None

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # ── APK 配置 ──
        apk_frame = ttk.LabelFrame(main, text="APK 配置", padding=10)
        apk_frame.pack(fill=tk.X, pady=(0, 8))

        self._row(apk_frame, "应用名称", self.var_app_name, 0)
        self._row(apk_frame, "包    名", self.var_package, 1)
        self._row(apk_frame, "版 本 号", self.var_version, 2)
        self._row(apk_frame, "公 司 名", self.var_company, 3)
        self._file_row(apk_frame, "应用图标", self.var_icon_path, 4, self._browse_icon)

        self.icon_preview = ttk.Label(apk_frame, text="(无预览)")
        self.icon_preview.grid(row=5, column=1, sticky="w", pady=2)

        # ── 页面配置 ──
        page_frame = ttk.LabelFrame(main, text="页面配置 (HTML)", padding=10)
        page_frame.pack(fill=tk.X, pady=(0, 8))

        self._row(page_frame, "中 文 名", self.var_cn_name, 0)
        self._row(page_frame, "英 文 名", self.var_en_name, 1)
        self._row(page_frame, "页面版本", self.var_page_version, 2)
        self._row(page_frame, "公 司 名", self.var_page_company, 3)
        self._file_row(page_frame, "Logo路径", self.var_logo_path, 4, self._browse_logo)

        self.logo_preview = ttk.Label(page_frame, text="(无预览)")
        self.logo_preview.grid(row=5, column=1, sticky="w", pady=2)

        # ── 操作按钮 ──
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_frame, text="保存配置", command=self._save_config).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_frame, text="生成图标", command=self._gen_icons).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="构建 APK", command=self._build_apk).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="签名 APK", command=self._sign_apk).pack(side=tk.LEFT, padx=4)

        # ── 日志 ──
        log_frame = ttk.LabelFrame(main, text="日志", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _row(self, parent, label, var, row):
        ttk.Label(parent, text=label, width=14, anchor="e").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=3)
        ttk.Entry(parent, textvariable=var, width=50).grid(row=row, column=1, sticky="ew", pady=3)
        parent.columnconfigure(1, weight=1)

    def _file_row(self, parent, label, var, row, browse_cmd):
        ttk.Label(parent, text=label, width=14, anchor="e").grid(row=row, column=0, sticky="e", padx=(0, 8), pady=3)
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Entry(frame, textvariable=var, width=38).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame, text="浏览", command=browse_cmd, width=6).pack(side=tk.LEFT, padx=(4, 0))
        parent.columnconfigure(1, weight=1)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    # ── 加载当前值 ──

    def _load_values(self):
        try:
            tauri = read_tauri_conf()
            dist = read_dist_config()
            strings = read_strings_xml()
            app_id = read_application_id()

            self.var_app_name.set(tauri.get("productName", ""))
            self.var_package.set(tauri.get("identifier", "") or app_id)
            self.var_version.set(tauri.get("version", ""))
            self.var_company.set(tauri.get("bundle", {}).get("copyright", ""))

            default_icon = str(ROOT / "src-tauri" / "icons" / "256x256.png")
            if os.path.isfile(default_icon):
                self.var_icon_path.set(default_icon)
                self._show_icon_preview(default_icon)

            self.var_cn_name.set(dist.get("systemName", ""))
            self.var_en_name.set(dist.get("systemNameEn", ""))
            self.var_page_version.set(tauri.get("version", ""))
            self.var_page_company.set(dist.get("copyright", ""))

            self.log("已从项目文件加载配置。")
        except Exception as e:
            self.log(f"加载出错: {e}")

    # ── 文件浏览 ──

    def _browse_icon(self):
        path = filedialog.askopenfilename(
            title="选择应用图标",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.ico"), ("所有文件", "*.*")]
        )
        if path:
            self.var_icon_path.set(path)
            self._show_icon_preview(path)

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="选择 Logo",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.ico"), ("所有文件", "*.*")]
        )
        if path:
            self.var_logo_path.set(path)
            self._show_logo_preview(path)

    def _show_icon_preview(self, path):
        try:
            img = Image.open(path).resize((48, 48), Image.LANCZOS)
            self.icon_preview_img = ImageTk.PhotoImage(img)
            self.icon_preview.config(image=self.icon_preview_img, text="")
        except Exception:
            self.icon_preview.config(text="(预览失败)")

    def _show_logo_preview(self, path):
        try:
            img = Image.open(path).resize((48, 48), Image.LANCZOS)
            self.logo_preview_img = ImageTk.PhotoImage(img)
            self.logo_preview.config(image=self.logo_preview_img, text="")
        except Exception:
            self.logo_preview.config(text="(预览失败)")

    # ── 操作 ──

    def _save_config(self):
        try:
            app_name = self.var_app_name.get().strip()
            package = self.var_package.get().strip()
            version = self.var_version.get().strip()
            company = self.var_company.get().strip()
            cn_name = self.var_cn_name.get().strip()
            en_name = self.var_en_name.get().strip()
            page_company = self.var_page_company.get().strip()
            logo_path = self.var_logo_path.get().strip()

            if not app_name or not package or not version:
                messagebox.showerror("错误", "应用名称、包名、版本号为必填项。")
                return

            self.log("--- 保存配置 ---")

            write_tauri_conf(app_name, version, package, company)
            self.log("[OK] tauri.conf.json")

            write_cargo_toml(app_name, version)
            self.log("[OK] Cargo.toml")

            if MAIN_RS.exists():
                write_main_rs_title(app_name)
                self.log("[OK] main.rs 窗口标题")

            write_strings_xml(app_name)
            self.log("[OK] strings.xml")

            write_application_id(package)
            self.log("[OK] build.gradle.kts applicationId")

            write_dist_config(cn_name, en_name, page_company)
            self.log("[OK] dist/config.json")

            write_dist_index_title(cn_name)
            self.log("[OK] dist/index.html <title>")

            sync_index_html()
            self.log("[OK] index.html 已同步")

            if logo_path and os.path.isfile(logo_path):
                update_logo_in_config(logo_path)
                self.log("[OK] logoUrl 已写入 config.json")

            self.var_page_version.set(version)

            self.log("--- 配置已保存 ---")
            messagebox.showinfo("完成", "配置已保存。")
        except Exception as e:
            self.log(f"保存出错: {e}")
            messagebox.showerror("错误", str(e))

    def _gen_icons(self):
        icon_path = self.var_icon_path.get().strip()
        res_dir = str(ROOT / "src-tauri" / "gen" / "android" / "app" / "src" / "main" / "res")

        if not icon_path or not os.path.isfile(icon_path):
            messagebox.showerror("错误", "请先选择应用图标文件。")
            return
        if not os.path.isdir(res_dir):
            messagebox.showerror("错误", f"Android res 目录不存在:\n{res_dir}")
            return

        try:
            self.log("--- 生成 Android 图标 ---")
            generate_android_icons(icon_path, res_dir, log_fn=self.log)
            self.log("--- 图标生成完成 ---")
            messagebox.showinfo("完成", "Android 图标已生成（16 个文件）。")
        except Exception as e:
            self.log(f"图标生成出错: {e}")
            messagebox.showerror("错误", str(e))

    def _run_in_thread(self, cmd, cwd, label, on_done=None):
        def worker():
            self.log(f"--- {label} ---")
            self.log(f"$ {cmd}")
            try:
                env = os.environ.copy()
                env["HTTP_PROXY"] = "http://127.0.0.1:7897"
                env["HTTPS_PROXY"] = "http://127.0.0.1:7897"
                proc = subprocess.Popen(
                    cmd, shell=True, cwd=cwd, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    encoding="utf-8", errors="replace",
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    if line:
                        self.log(line)
                proc.wait()
                if proc.returncode == 0:
                    self.log(f"--- {label}: 成功 ---")
                    if on_done:
                        self.root.after(0, on_done)
                else:
                    self.log(f"--- {label}: 失败 (退出码 {proc.returncode}) ---")
            except Exception as e:
                self.log(f"--- {label}: 错误: {e} ---")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _build_apk(self):
        app_name = self.var_app_name.get().strip()
        if not app_name:
            messagebox.showerror("错误", "请先填写应用名称。")
            return

        MAIN_RS.touch()

        self._run_in_thread(
            "cargo tauri android build",
            str(ROOT / "src-tauri"),
            "构建 APK",
        )

    def _sign_apk(self):
        apk_dir = ROOT / "src-tauri" / "gen" / "android" / "app" / "build" / "outputs" / "apk" / "universal" / "release"
        unsigned = apk_dir / "app-universal-release-unsigned.apk"

        if not unsigned.exists():
            messagebox.showerror("错误", f"未找到未签名 APK:\n{unsigned}\n\n请先构建。")
            return

        sdk = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/AppData/Local/Android/Sdk")
        bt_dir = None
        bt_base = Path(sdk) / "build-tools"
        if bt_base.exists():
            versions = sorted(bt_base.iterdir(), reverse=True)
            for v in versions:
                if (v / "apksigner.bat").exists():
                    bt_dir = v
                    break

        if not bt_dir:
            messagebox.showerror("错误", "未找到 Android build-tools。\n请设置 ANDROID_HOME 环境变量。")
            return

        aligned = apk_dir / "app-universal-release-aligned.apk"
        signed = apk_dir / "app-universal-release-signed.apk"

        if not KEYSTORE.exists():
            messagebox.showerror("错误", f"未找到签名密钥库:\n{KEYSTORE}")
            return

        zipalign = str(bt_dir / "zipalign")
        apksigner = str(bt_dir / "apksigner.bat")

        def do_sign():
            self.log("--- 签名 APK ---")
            try:
                self.log(f"$ zipalign -f 4 {unsigned.name} {aligned.name}")
                r = subprocess.run(
                    [zipalign, "-f", "4", str(unsigned), str(aligned)],
                    capture_output=True, text=True,
                )
                if r.returncode != 0:
                    self.log(f"zipalign 出错: {r.stderr}")
                    return
                self.log("[OK] zipalign 对齐完成")

                self.log("$ apksigner sign ...")
                r = subprocess.run(
                    [apksigner, "sign",
                     "--ks", str(KEYSTORE),
                     "--ks-key-alias", "shinecaniep",
                     "--ks-pass", "pass:shinecaniep",
                     "--key-pass", "pass:shinecaniep",
                     "--out", str(signed),
                     str(aligned)],
                    capture_output=True, text=True,
                )
                if r.returncode != 0:
                    self.log(f"apksigner 出错: {r.stderr}")
                    return
                self.log("[OK] 签名完成")

                r = subprocess.run(
                    [apksigner, "verify", "--print-certs", str(signed)],
                    capture_output=True, text=True,
                )
                for line in r.stdout.strip().split("\n"):
                    self.log(line)

                size_mb = signed.stat().st_size / (1024 * 1024)
                self.log(f"--- 签名完成: {signed} ({size_mb:.1f} MB) ---")

            except Exception as e:
                self.log(f"签名出错: {e}")

        t = threading.Thread(target=do_sign, daemon=True)
        t.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BuildGUI()
    app.run()
