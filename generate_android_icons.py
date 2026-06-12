#!/usr/bin/env python3
"""
Android APK 图标生成脚本
从源图标生成所有 mipmap 密度的 Android 图标

用法：
  python generate_android_icons.py

交互式输入：
  1. 源图标路径（默认 src-tauri/icons/256x256.png）
  2. Android res 目录路径（自动检测或手动输入）
  3. 背景色（默认透明）
"""

import os
import sys
import glob

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow required, run: pip install Pillow")
    sys.exit(1)


# ── Android 标准图标尺寸 ──────────────────────────────────────────────

# ic_launcher.png — 标准启动图标
LAUNCHER_SIZES = {
    "mdpi":    48,
    "hdpi":    72,
    "xhdpi":   96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

# ic_launcher_foreground.png — 自适应图标前景层（108dp 画布，图标居中）
FOREGROUND_CANVAS = {
    "mdpi":    108,
    "hdpi":    162,
    "xhdpi":   216,
    "xxhdpi":  324,
    "xxxhdpi": 432,
}

# ic_launcher_round.png — 圆形图标（与 launcher 同尺寸，圆形裁切）

# 源图标中图标内容的安全区域比例（自适应图标规范：中心 72dp / 108dp ≈ 66.7%）
ICON_SAFE_RATIO = 0.625


def find_android_res_dir():
    """自动检测 Android res 目录"""
    candidates = glob.glob("src-tauri/gen/android/app/src/main/res")
    if candidates:
        return candidates[0]
    return None


def prompt_input(label, default=None):
    """交互式输入，支持默认值"""
    if default:
        prompt = f"  {label} [{default}]: "
    else:
        prompt = f"  {label}: "
    value = input(prompt).strip().strip('"').strip("'")
    return value if value else default


def generate_icons(src_path, res_dir, bg_color_hex):
    """生成所有密度的 Android 图标"""

    if not os.path.isfile(src_path):
        print(f"\nError: source icon not found: {src_path}")
        sys.exit(1)

    if not os.path.isdir(res_dir):
        print(f"\nError: res dir not found: {res_dir}")
        sys.exit(1)

    src = Image.open(src_path).convert("RGBA")
    print(f"\nSource: {src_path} ({src.size[0]}x{src.size[1]})")

    # 解析背景色
    bg_color = parse_color(bg_color_hex)

    total = 0

    for density in LAUNCHER_SIZES:
        mipmap_dir = os.path.join(res_dir, f"mipmap-{density}")
        os.makedirs(mipmap_dir, exist_ok=True)

        size = LAUNCHER_SIZES[density]
        canvas = FOREGROUND_CANVAS[density]
        icon_inner = int(canvas * ICON_SAFE_RATIO)

        # ── 1. ic_launcher.png ──
        icon = src.resize((size, size), Image.LANCZOS)
        # 如果指定了背景色，合成到底层
        if bg_color[3] > 0:
            bg = Image.new("RGBA", (size, size), bg_color)
            icon = Image.alpha_composite(bg, icon)
        icon.save(os.path.join(mipmap_dir, "ic_launcher.png"))
        print(f"  [OK] mipmap-{density}/ic_launcher.png         {size}x{size}")
        total += 1

        # ── 2. ic_launcher_round.png ──
        round_icon = src.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
        if bg_color[3] > 0:
            round_bg = Image.new("RGBA", (size, size), bg_color)
            round_icon = Image.alpha_composite(round_bg, round_icon)
        round_icon.putalpha(mask)
        round_icon.save(os.path.join(mipmap_dir, "ic_launcher_round.png"))
        print(f"  [OK] mipmap-{density}/ic_launcher_round.png    {size}x{size}")
        total += 1

        # ── 3. ic_launcher_foreground.png ──
        icon_fg = src.resize((icon_inner, icon_inner), Image.LANCZOS)
        fg = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        offset = (canvas - icon_inner) // 2
        fg.paste(icon_fg, (offset, offset), icon_fg if icon_fg.mode == "RGBA" else None)
        fg.save(os.path.join(mipmap_dir, "ic_launcher_foreground.png"))
        print(f"  [OK] mipmap-{density}/ic_launcher_foreground.png {canvas}x{canvas}")
        total += 1

    # ── 4. 更新 ic_launcher_background.xml ──
    bg_xml_path = os.path.join(res_dir, "drawable", "ic_launcher_background.xml")
    os.makedirs(os.path.dirname(bg_xml_path), exist_ok=True)
    write_background_xml(bg_xml_path, bg_color_hex, bg_color)
    print(f"  [OK] drawable/ic_launcher_background.xml  bg={bg_color_hex}")
    total += 1

    print(f"\nDone! {total} files generated.")


def parse_color(hex_str):
    """解析颜色字符串，返回 RGBA 元组"""
    hex_str = hex_str.lstrip("#").lower()
    if hex_str in ("transparent", "none", "00000000"):
        return (0, 0, 0, 0)
    if len(hex_str) == 6:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        return (r, g, b, 255)
    if len(hex_str) == 8:
        r, g, b, a = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16)
        return (r, g, b, a)
    return (0, 0, 0, 0)


def write_background_xml(path, hex_str, rgba):
    """写入 ic_launcher_background.xml"""
    if rgba[3] == 0:
        color = "#00000000"
    else:
        color = f"#{rgba[0]:02X}{rgba[1]:02X}{rgba[2]:02X}"
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="{color}"
        android:pathData="M0,0h108v108h-108z" />
</vector>
'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print("=" * 50)
    print("  Android APK Icon Generator")
    print("=" * 50)
    print()

    # 1. 源图标
    default_src = "src-tauri/icons/256x256.png"
    if not os.path.isfile(default_src):
        default_src = ""
    src_path = prompt_input("Source icon path", default_src or None)
    if not src_path:
        print("Error: source icon path required")
        sys.exit(1)

    # 2. Android res 目录
    auto_res = find_android_res_dir()
    if auto_res:
        print(f"  Auto-detected: {auto_res}")
    res_dir = prompt_input("Android res dir", auto_res)
    if not res_dir:
        print("Error: Android res dir required")
        sys.exit(1)

    # 3. background color
    print()
    print("  Adaptive icon background (transparent = icon only, no background)")
    print("  Examples: transparent / #FFFFFF / #1890FF / #3DDC84")
    bg_color = prompt_input("Background color", "transparent")

    generate_icons(src_path, res_dir, bg_color)


if __name__ == "__main__":
    main()
