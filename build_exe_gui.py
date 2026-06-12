#!/usr/bin/env python3
"""
EXE / Windows 安装包打包 GUI
基于 build.js 逻辑，可视化配置 + 一键构建

用法: python build_exe_gui.py
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
from PIL import Image, ImageTk

# ── 项目路径 ──
ROOT = Path(__file__).parent.resolve()
TAURI_CONF = ROOT / "src-tauri" / "tauri.conf.json"
CARGO_TOML = ROOT / "src-tauri" / "Cargo.toml"
LIB_RS = ROOT / "src-tauri" / "src" / "lib.rs"
DIST_CONFIG = ROOT / "dist" / "config.json"
DIST_INDEX = ROOT / "dist" / "index.html"
ROOT_INDEX = ROOT / "index.html"


# ══════════════════════════════════════════════════════════════
#  Config readers
# ══════════════════════════════════════════════════════════════

def read_tauri_conf():
    with open(TAURI_CONF, "r", encoding="utf-8") as f:
        return json.load(f)

def read_dist_config():
    with open(DIST_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
#  Config writers (from build.js logic)
# ══════════════════════════════════════════════════════════════

def write_tauri_conf(product_name, version, copyright_):
    content = TAURI_CONF.read_text(encoding="utf-8")
    content = re.sub(r'"productName"\s*:\s*"[^"]*"', f'"productName": "{product_name}"', content)
    content = re.sub(r'"version"\s*:\s*"[^"]*"', f'"version": "{version}"', content)
    if copyright_:
        content = re.sub(r'"copyright"\s*:\s*"[^"]*"', f'"copyright": "{copyright_}"', content)
    TAURI_CONF.write_text(content, encoding="utf-8")

def write_cargo_toml(name, version):
    content = CARGO_TOML.read_text(encoding="utf-8")
    content = re.sub(r'^name\s*=\s*"[^"]*"', f'name = "{name}"', content, flags=re.MULTILINE)
    content = re.sub(r'^version\s*=\s*"[^"]*"', f'version = "{version}"', content, flags=re.MULTILINE)
    content = re.sub(r'^description\s*=\s*"[^"]*"', f'description = "{name}"', content, flags=re.MULTILINE)
    CARGO_TOML.write_text(content, encoding="utf-8")

def write_lib_rs_title(title):
    if not LIB_RS.exists():
        return False
    content = LIB_RS.read_text(encoding="utf-8")
    new_content = re.sub(r'\.title\("[^"]*"\)', f'.title("{title}")', content)
    if new_content != content:
        LIB_RS.write_text(new_content, encoding="utf-8")
        return True
    return False

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

def sync_index_html():
    if DIST_INDEX.exists():
        ROOT_INDEX.write_text(DIST_INDEX.read_text(encoding="utf-8"), encoding="utf-8")

def update_logo_in_config(logo_path):
    if not logo_path or not os.path.isfile(logo_path):
        return False
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
    return True


# ══════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════

class ExeBuildGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EXE 打包工具")
        self.root.geometry("720x780")
        self.root.resizable(True, True)
        self.root.minsize(600, 680)

        self.var_clean_build = tk.BooleanVar(value=False)

        self.var_cn_name = tk.StringVar()
        self.var_en_name = tk.StringVar()
        self.var_version = tk.StringVar()
        self.var_company = tk.StringVar()
        self.var_logo_path = tk.StringVar()

        self.logo_preview_img = None
        self._building = False

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # ── 应用信息 ──
        info_frame = ttk.LabelFrame(main, text="应用信息", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 8))

        self._row(info_frame, "中 文 名", self.var_cn_name, 0)
        self._row(info_frame, "英 文 名", self.var_en_name, 1)
        self._row(info_frame, "版 本 号", self.var_version, 2)
        self._row(info_frame, "公 司 名", self.var_company, 3)
        self._file_row(info_frame, "Logo", self.var_logo_path, 4, self._browse_logo)

        self.logo_preview = ttk.Label(info_frame, text="(无预览)")
        self.logo_preview.grid(row=5, column=1, sticky="w", pady=2)

        # ── 构建选项 ──
        opt_frame = ttk.LabelFrame(main, text="构建选项", padding=10)
        opt_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Checkbutton(opt_frame, text="构建前执行 cargo clean（修改过 dist/ 文件后建议勾选）",
                         variable=self.var_clean_build).pack(anchor="w")

        # ── 输出文件 ──
        out_frame = ttk.LabelFrame(main, text="输出文件", padding=10)
        out_frame.pack(fill=tk.X, pady=(0, 8))

        self.lbl_exe = ttk.Label(out_frame, text="可执行文件: (尚未构建)", wraplength=600, font=("Consolas", 9))
        self.lbl_exe.pack(anchor="w", pady=1)
        self.lbl_nsis = ttk.Label(out_frame, text="安装包:     (尚未构建)", wraplength=600, font=("Consolas", 9))
        self.lbl_nsis.pack(anchor="w", pady=1)

        # ── 操作按钮 ──
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.btn_save = ttk.Button(btn_frame, text="保存配置", command=self._save_config)
        self.btn_save.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_build = ttk.Button(btn_frame, text="构建 EXE", command=self._build)
        self.btn_build.pack(side=tk.LEFT, padx=4)

        self.btn_open = ttk.Button(btn_frame, text="打开输出目录", command=self._open_output)
        self.btn_open.pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_frame, text="运行 EXE", command=self._run_exe).pack(side=tk.LEFT, padx=4)

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

    # ── 加载 ──

    def _load_values(self):
        try:
            tauri = read_tauri_conf()
            dist = read_dist_config()

            self.var_cn_name.set(tauri.get("productName", ""))
            self.var_version.set(tauri.get("version", ""))
            self.var_company.set(tauri.get("bundle", {}).get("copyright", ""))

            self.var_en_name.set(dist.get("systemNameEn", ""))

            self._update_output_labels()
            self.log("已从项目文件加载配置。")
        except Exception as e:
            self.log(f"加载出错: {e}")

    def _update_output_labels(self):
        name = self.var_cn_name.get().strip() or "app"
        ver = self.var_version.get().strip() or "0.0.0"
        release = ROOT / "src-tauri" / "target" / "release"
        nsis = release / "bundle" / "nsis"
        self.lbl_exe.config(text=f"可执行文件: {release / (name + '.exe')}")
        self.lbl_nsis.config(text=f"安装包:     {nsis / (name + '_' + ver + '_x64-setup.exe')}")

    # ── 浏览 ──

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title="选择 Logo",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.ico"), ("所有文件", "*.*")]
        )
        if path:
            self.var_logo_path.set(path)
            try:
                img = Image.open(path).resize((48, 48), Image.LANCZOS)
                self.logo_preview_img = ImageTk.PhotoImage(img)
                self.logo_preview.config(image=self.logo_preview_img, text="")
            except Exception:
                self.logo_preview.config(text="(预览失败)")

    # ── 保存 ──

    def _save_config(self):
        try:
            cn = self.var_cn_name.get().strip()
            en = self.var_en_name.get().strip()
            ver = self.var_version.get().strip()
            company = self.var_company.get().strip()
            logo = self.var_logo_path.get().strip()

            if not cn or not ver:
                messagebox.showerror("错误", "中文名和版本号为必填项。")
                return

            if not re.match(r"^\d+\.\d+\.\d+", ver):
                messagebox.showerror("错误", f'版本号格式无效: "{ver}"\n应为 x.y.z 格式')
                return

            self.log("--- 保存配置 ---")

            write_tauri_conf(cn, ver, company)
            self.log("[OK] tauri.conf.json")

            write_cargo_toml(cn, ver)
            self.log("[OK] Cargo.toml")

            if LIB_RS.exists():
                changed = write_lib_rs_title(cn)
                self.log(f"[{'OK' if changed else '--'}] lib.rs 窗口标题")

            write_dist_config(cn, en, company)
            self.log("[OK] dist/config.json")

            write_dist_index_title(cn)
            self.log("[OK] dist/index.html <title>")

            sync_index_html()
            self.log("[OK] index.html 已同步")

            if logo and os.path.isfile(logo):
                update_logo_in_config(logo)
                self.log("[OK] logoUrl -> config.json")

            self._update_output_labels()
            self.log("--- 配置已保存 ---")
            messagebox.showinfo("完成", "配置已保存。")
        except Exception as e:
            self.log(f"保存出错: {e}")
            messagebox.showerror("错误", str(e))

    # ── 构建 ──

    def _build(self):
        if self._building:
            messagebox.showinfo("提示", "正在构建中，请稍候。")
            return

        cn = self.var_cn_name.get().strip()
        ver = self.var_version.get().strip()
        if not cn or not ver:
            messagebox.showerror("错误", "请先保存配置。")
            return

        self._building = True
        self.btn_build.config(state="disabled")

        def worker():
            try:
                if self.var_clean_build.get():
                    self.log("--- 执行 cargo clean ---")
                    proc = subprocess.run(
                        ["cargo", "clean"],
                        cwd=str(ROOT / "src-tauri"),
                        capture_output=True, text=True,
                    )
                    self.log("cargo clean 完成" if proc.returncode == 0 else f"clean 出错: {proc.stderr}")

                self.log("--- 开始构建 EXE（需要几分钟） ---")
                self.log("$ cargo tauri build")
                proc = subprocess.Popen(
                    ["cargo", "tauri", "build"],
                    cwd=str(ROOT / "src-tauri"),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    encoding="utf-8", errors="replace",
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    if line:
                        self.log(line)
                proc.wait()

                if proc.returncode == 0:
                    self.log("--- 构建成功 ---")
                    self.root.after(0, self._on_build_success)
                else:
                    self.log(f"--- 构建失败 (退出码 {proc.returncode}) ---")
            except Exception as e:
                self.log(f"构建出错: {e}")
            finally:
                self._building = False
                self.root.after(0, lambda: self.btn_build.config(state="normal"))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_build_success(self):
        cn = self.var_cn_name.get().strip()
        ver = self.var_version.get().strip()
        release = ROOT / "src-tauri" / "target" / "release"
        nsis = release / "bundle" / "nsis"
        exe_path = release / f"{cn}.exe"
        nsis_path = nsis / f"{cn}_{ver}_x64-setup.exe"

        self.lbl_exe.config(text=f"可执行文件: {exe_path}")
        self.lbl_nsis.config(text=f"安装包:     {nsis_path}")

        msgs = []
        if exe_path.exists():
            msgs.append(f"EXE: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        if nsis_path.exists():
            msgs.append(f"NSIS 安装包: {nsis_path.stat().st_size / 1024 / 1024:.1f} MB")

        if msgs:
            messagebox.showinfo("构建完成", "\n".join(msgs))
        else:
            if nsis.exists():
                files = list(nsis.glob("*.exe"))
                if files:
                    self.lbl_nsis.config(text=f"安装包:     {files[0]}")
                    messagebox.showinfo("构建完成", f"安装包: {files[0]}")

    # ── 打开 / 运行 ──

    def _open_output(self):
        import subprocess as sp
        nsis_dir = ROOT / "src-tauri" / "target" / "release" / "bundle" / "nsis"
        release_dir = ROOT / "src-tauri" / "target" / "release"
        target = nsis_dir if nsis_dir.exists() else release_dir
        os.makedirs(target, exist_ok=True)
        sp.Popen(["explorer", str(target)])

    def _run_exe(self):
        cn = self.var_cn_name.get().strip()
        exe = ROOT / "src-tauri" / "target" / "release" / f"{cn}.exe"
        if not exe.exists():
            messagebox.showerror("错误", f"未找到 EXE:\n{exe}\n\n请先构建。")
            return
        subprocess.Popen([str(exe)])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ExeBuildGUI()
    app.run()
