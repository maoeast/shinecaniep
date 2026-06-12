#!/usr/bin/env python3
"""
APK 打包命令行工具
可视化配置应用信息、生成图标、构建签名 APK

用法: python3 build_apk_cli.py
"""

import os
import sys
import json
import re
import subprocess
import base64
from pathlib import Path
from PIL import Image, ImageDraw

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

LAUNCHER_SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND_CANVAS = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
ICON_SAFE_RATIO = 0.625


# ══════════════════════════════════════════════════════════════
#  Colors
# ══════════════════════════════════════════════════════════════

def c(code, text):
    return f"\033[{code}m{text}\033[0m"

GREEN = lambda t: c("32", t)
YELLOW = lambda t: c("33", t)
RED = lambda t: c("31", t)
CYAN = lambda t: c("36", t)
BOLD = lambda t: c("1", t)
DIM = lambda t: c("2", t)


# ══════════════════════════════════════════════════════════════
#  Config readers
# ══════════════════════════════════════════════════════════════

def read_tauri_conf():
    return json.loads(safe_read(TAURI_CONF))

def read_dist_config():
    return json.loads(safe_read(DIST_CONFIG))

def read_strings_xml():
    if not STRINGS_XML.exists():
        return {"app_name": "", "main_activity_title": ""}
    content = safe_read(STRINGS_XML)
    app_name = re.search(r'name="app_name"[^>]*>([^<]+)', content)
    title = re.search(r'name="main_activity_title"[^>]*>([^<]+)', content)
    return {
        "app_name": app_name.group(1) if app_name else "",
        "main_activity_title": title.group(1) if title else "",
    }

def read_application_id():
    if not BUILD_GRADLE.exists():
        return ""
    content = safe_read(BUILD_GRADLE)
    m = re.search(r'applicationId\s*=\s*"([^"]+)"', content)
    return m.group(1) if m else ""


# ══════════════════════════════════════════════════════════════
#  Config writers
# ══════════════════════════════════════════════════════════════

def safe_read(path):
    return path.read_text(encoding="utf-8", errors="replace")

def safe_write(path, content):
    path.write_text(content, encoding="utf-8", errors="replace")

def write_tauri_conf(product_name, version, identifier, copyright_):
    content = safe_read(TAURI_CONF)
    content = re.sub(r'"productName"\s*:\s*"[^"]*"', f'"productName": "{product_name}"', content)
    content = re.sub(r'"version"\s*:\s*"[^"]*"', f'"version": "{version}"', content)
    content = re.sub(r'"identifier"\s*:\s*"[^"]*"', f'"identifier": "{identifier}"', content)
    if copyright_:
        content = re.sub(r'"copyright"\s*:\s*"[^"]*"', f'"copyright": "{copyright_}"', content)
    safe_write(TAURI_CONF, content)

def write_cargo_toml(name, version):
    content = safe_read(CARGO_TOML)
    content = re.sub(r'^name\s*=\s*"[^"]*"', f'name = "{name}"', content, flags=re.MULTILINE)
    content = re.sub(r'^version\s*=\s*"[^"]*"', f'version = "{version}"', content, flags=re.MULTILINE)
    content = re.sub(r'^description\s*=\s*"[^"]*"', f'description = "{name}"', content, flags=re.MULTILINE)
    safe_write(CARGO_TOML, content)

def write_main_rs_title(title):
    content = safe_read(MAIN_RS)
    content = re.sub(r'\.title\("[^"]*"\)', f'.title("{title}")', content)
    safe_write(MAIN_RS, content)

def write_dist_config(system_name, system_name_en, copyright_):
    config = read_dist_config()
    config["systemName"] = system_name
    config["systemNameEn"] = system_name_en
    if copyright_:
        config["copyright"] = copyright_
    DIST_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8", errors="replace")

def write_dist_index_title(title):
    content = safe_read(DIST_INDEX)
    content = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", content)
    safe_write(DIST_INDEX, content)

def write_strings_xml(app_name):
    if not STRINGS_XML.exists():
        return
    content = safe_read(STRINGS_XML)
    content = re.sub(r'(<string name="app_name">)[^<]*(</string>)', rf'\g<1>{app_name}\g<2>', content)
    content = re.sub(r'(<string name="main_activity_title">)[^<]*(</string>)', rf'\g<1>{app_name}\g<2>', content)
    safe_write(STRINGS_XML, content)

def write_application_id(app_id):
    if not BUILD_GRADLE.exists():
        return
    content = safe_read(BUILD_GRADLE)
    content = re.sub(r'applicationId\s*=\s*"[^"]*"', f'applicationId = "{app_id}"', content)
    safe_write(BUILD_GRADLE, content)

def sync_index_html():
    if DIST_INDEX.exists():
        safe_write(ROOT_INDEX, safe_read(DIST_INDEX))

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
    DIST_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8", errors="replace")


# ══════════════════════════════════════════════════════════════
#  Icon generation
# ══════════════════════════════════════════════════════════════

def generate_android_icons(src_path, res_dir):
    src = Image.open(src_path).convert("RGBA")
    print(GREEN(f"  源图标: {src.size[0]}x{src.size[1]}"))

    for density, size in LAUNCHER_SIZES.items():
        mipmap_dir = os.path.join(res_dir, f"mipmap-{density}")
        os.makedirs(mipmap_dir, exist_ok=True)
        canvas = FOREGROUND_CANVAS[density]
        icon_inner = int(canvas * ICON_SAFE_RATIO)

        icon = src.resize((size, size), Image.LANCZOS)
        icon.save(os.path.join(mipmap_dir, "ic_launcher.png"))

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
    print(GREEN(f"  已生成 16 个图标文件"))


# ══════════════════════════════════════════════════════════════
#  Input helpers
# ══════════════════════════════════════════════════════════════

def prompt(label, default=""):
    suffix = f" [{default}]" if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val if val else default

def confirm(msg):
    return input(f"  {msg} (y/N): ").strip().lower() in ("y", "yes")


# ══════════════════════════════════════════════════════════════
#  Actions
# ══════════════════════════════════════════════════════════════

def action_save_config():
    tauri = read_tauri_conf()
    dist = read_dist_config()

    print(BOLD("\n── APK 配置 ──"))
    app_name = prompt("应用名称", tauri.get("productName", ""))
    package = prompt("包    名", tauri.get("identifier", "") or read_application_id())
    version = prompt("版 本 号", tauri.get("version", ""))
    company = prompt("公 司 名", tauri.get("bundle", {}).get("copyright", ""))

    print(BOLD("\n── 页面配置 ──"))
    cn_name = prompt("中 文 名", dist.get("systemName", ""))
    en_name = prompt("英 文 名", dist.get("systemNameEn", ""))
    page_company = prompt("公 司 名", dist.get("copyright", ""))
    logo_path = prompt("Logo路径 (留空跳过)", "")

    if not app_name or not package or not version:
        print(RED("错误: 应用名称、包名、版本号为必填项"))
        return

    print(YELLOW("\n保存中..."))
    write_tauri_conf(app_name, version, package, company)
    print(GREEN("  [OK] tauri.conf.json"))

    write_cargo_toml(app_name, version)
    print(GREEN("  [OK] Cargo.toml"))

    if MAIN_RS.exists():
        write_main_rs_title(app_name)
        print(GREEN("  [OK] main.rs 窗口标题"))

    write_strings_xml(app_name)
    print(GREEN("  [OK] strings.xml"))

    write_application_id(package)
    print(GREEN("  [OK] build.gradle.kts applicationId"))

    write_dist_config(cn_name, en_name, page_company)
    print(GREEN("  [OK] dist/config.json"))

    write_dist_index_title(cn_name)
    print(GREEN("  [OK] dist/index.html <title>"))

    sync_index_html()
    print(GREEN("  [OK] index.html 已同步"))

    if logo_path and os.path.isfile(logo_path):
        update_logo_in_config(logo_path)
        print(GREEN("  [OK] logoUrl 已写入 config.json"))

    print(GREEN("\n配置已保存!"))


def action_gen_icons():
    icon_path = prompt("选择图标文件路径 (png/jpg)", str(ROOT / "src-tauri" / "icons" / "256x256.png"))
    if not icon_path or not os.path.isfile(icon_path):
        print(RED("图标文件不存在"))
        return

    res_dir = str(ROOT / "src-tauri" / "gen" / "android" / "app" / "src" / "main" / "res")
    if not os.path.isdir(res_dir):
        print(RED(f"Android res 目录不存在: {res_dir}"))
        return

    print(YELLOW("\n生成图标中..."))
    generate_android_icons(icon_path, res_dir)
    print(GREEN("\n图标生成完成!"))


def action_build_apk():
    print(YELLOW("\n开始构建 APK (首次编译较慢)..."))
    MAIN_RS.touch()

    env = os.environ.copy()
    proc = subprocess.Popen(
        "cargo tauri android build",
        shell=True, cwd=str(ROOT / "src-tauri"), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            print(f"  {line}")
    proc.wait()

    if proc.returncode == 0:
        print(GREEN("\nAPK 构建成功!"))
    else:
        print(RED(f"\n构建失败 (退出码 {proc.returncode})"))


def action_sign_apk():
    apk_dir = ROOT / "src-tauri" / "gen" / "android" / "app" / "build" / "outputs" / "apk" / "universal" / "release"
    unsigned = apk_dir / "app-universal-release-unsigned.apk"

    if not unsigned.exists():
        print(RED(f"未找到未签名 APK: {unsigned}"))
        print(DIM("请先构建 APK"))
        return

    sdk = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/android-sdk")
    bt_dir = None
    bt_base = Path(sdk) / "build-tools"
    if bt_base.exists():
        versions = sorted(bt_base.iterdir(), reverse=True)
        for v in versions:
            signer = v / "apksigner" if sys.platform != "win32" else v / "apksigner.bat"
            if signer.exists():
                bt_dir = v
                break

    if not bt_dir:
        print(RED("未找到 Android build-tools，请设置 ANDROID_HOME 环境变量"))
        return

    aligned = apk_dir / "app-universal-release-aligned.apk"
    signed = apk_dir / "app-universal-release-signed.apk"

    if not KEYSTORE.exists():
        print(RED(f"未找到签名密钥库: {KEYSTORE}"))
        return

    zipalign = str(bt_dir / "zipalign")
    apksigner = str(bt_dir / "apksigner") if sys.platform != "win32" else str(bt_dir / "apksigner.bat")

    print(YELLOW("\n签名中..."))

    r = subprocess.run([zipalign, "-f", "4", str(unsigned), str(aligned)], capture_output=True, text=True)
    if r.returncode != 0:
        print(RED(f"zipalign 出错: {r.stderr}"))
        return
    print(GREEN("  [OK] zipalign 对齐完成"))

    r = subprocess.run([
        apksigner, "sign",
        "--ks", str(KEYSTORE),
        "--ks-key-alias", "shinecaniep",
        "--ks-pass", "pass:shinecaniep",
        "--key-pass", "pass:shinecaniep",
        "--out", str(signed),
        str(aligned),
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(RED(f"apksigner 出错: {r.stderr}"))
        return
    print(GREEN("  [OK] 签名完成"))

    r = subprocess.run([apksigner, "verify", "--print-certs", str(signed)], capture_output=True, text=True)
    for line in r.stdout.strip().split("\n"):
        print(f"  {line}")

    size_mb = signed.stat().st_size / (1024 * 1024)
    print(GREEN(f"\n签名完成: {signed} ({size_mb:.1f} MB)"))

    # 询问是否复制到 Windows 桌面
    if confirm("复制到 Windows 桌面?"):
        desktop = Path("/mnt/c/Users") / os.environ.get("USER", "maoea") / "Desktop"
        if not desktop.exists():
            # 尝试常见的 Windows 用户名
            for d in Path("/mnt/c/Users").iterdir():
                if d.name not in ("Public", "Default", "All Users", "Default User") and (d / "Desktop").exists():
                    desktop = d / "Desktop"
                    break
        if desktop.exists():
            import shutil
            dest = desktop / signed.name
            shutil.copy2(str(signed), str(dest))
            print(GREEN(f"已复制到: {dest}"))
        else:
            print(YELLOW("未找到 Windows 桌面路径，请手动复制"))


def action_copy_apk():
    signed = ROOT / "src-tauri" / "gen" / "android" / "app" / "build" / "outputs" / "apk" / "universal" / "release" / "app-universal-release-signed.apk"
    unsigned = ROOT / "src-tauri" / "gen" / "android" / "app" / "build" / "outputs" / "apk" / "universal" / "release" / "app-universal-release-unsigned.apk"

    src = signed if signed.exists() else unsigned
    if not src.exists():
        print(RED("未找到 APK 文件，请先构建"))
        return

    label = "已签名" if src == signed else "未签名"
    print(f"  APK ({label}): {src} ({src.stat().st_size / (1024*1024):.1f} MB)")

    desktop = Path("/mnt/c/Users") / os.environ.get("USER", "maoea") / "Desktop"
    if not desktop.exists():
        for d in Path("/mnt/c/Users").iterdir():
            if d.name not in ("Public", "Default", "All Users", "Default User") and (d / "Desktop").exists():
                desktop = d / "Desktop"
                break

    if desktop.exists():
        import shutil
        dest = desktop / src.name
        shutil.copy2(str(src), str(dest))
        print(GREEN(f"已复制到: {dest}"))
    else:
        print(YELLOW(f"未找到 Windows 桌面，手动复制: {src}"))


# ══════════════════════════════════════════════════════════════
#  Main menu
# ══════════════════════════════════════════════════════════════

def show_current_config():
    print(BOLD("  当前配置:"))
    tauri = read_tauri_conf()
    dist = read_dist_config()
    strings = read_strings_xml()
    app_id = read_application_id()
    print(f"    应用名称: {tauri.get('productName', '-')}")
    print(f"    包    名: {tauri.get('identifier', '-') or app_id}")
    print(f"    版 本 号: {tauri.get('version', '-')}")
    print(f"    公 司 名: {tauri.get('bundle', {}).get('copyright', '-')}")
    print(f"    Android名: {strings.get('app_name', '-')}")
    print(f"    页面中文名: {dist.get('systemName', '-')}")
    print(f"    页面英文名: {dist.get('systemNameEn', '-')}")


def main():
    print(BOLD("\n╔══════════════════════════════╗"))
    print(BOLD("║      APK 打包命令行工具       ║"))
    print(BOLD("╚══════════════════════════════╝"))

    while True:
        show_current_config()
        print(BOLD("\n  操作菜单:"))
        print("  1. 修改配置 (名称/包名/版本/公司/Logo)")
        print("  2. 生成 Android 图标")
        print("  3. 构建 APK")
        print("  4. 签名 APK")
        print("  5. 一键构建+签名")
        print("  6. 复制 APK 到 Windows 桌面")
        print("  0. 退出")

        choice = input("\n  请选择 [0-6]: ").strip()

        if choice == "1":
            action_save_config()
        elif choice == "2":
            action_gen_icons()
        elif choice == "3":
            action_build_apk()
        elif choice == "4":
            action_sign_apk()
        elif choice == "5":
            action_build_apk()
            apk_dir = ROOT / "src-tauri" / "gen" / "android" / "app" / "build" / "outputs" / "apk" / "universal" / "release"
            unsigned = apk_dir / "app-universal-release-unsigned.apk"
            if unsigned.exists():
                action_sign_apk()
        elif choice == "6":
            action_copy_apk()
        elif choice == "0":
            print(DIM("再见!"))
            break
        else:
            print(RED("无效选择"))

        input(DIM("\n按回车继续..."))


if __name__ == "__main__":
    main()
