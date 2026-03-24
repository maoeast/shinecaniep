#!/usr/bin/env python3
"""
图标生成脚本
从源图标生成 Tauri 所需的各种尺寸图标
"""

import os
import sys
import struct
from PIL import Image
import io


def create_icns(icon_path, output_path):
    """
    创建 macOS .icns 图标文件
    使用简单的 icns 文件格式实现
    """
    # 定义需要的尺寸和对应的类型标识
    icon_sizes = [
        (16, b'icp4'),      # 16x16
        (32, b'icp5'),      # 32x32
        (48, b'icp6'),      # 48x48
        (128, b'ic07'),     # 128x128
        (256, b'ic08'),     # 256x256
        (512, b'ic09'),     # 512x512
        (1024, b'ic10'),    # 1024x1024 (Retina)
    ]

    # 打开源图像
    source = Image.open(icon_path)

    # 对于 ICO 文件，Pillow 会自动选择最大尺寸
    # 我们直接使用加载的图像

    # 转换为 RGBA 模式
    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    # 生成各个尺寸的图标数据
    icon_data_list = []

    for size, icon_type in icon_sizes:
        # 调整图像大小
        resized = source.resize((size, size), Image.LANCZOS)

        # 保存为 PNG 格式（icns 使用 PNG 数据）
        buffer = io.BytesIO()
        resized.save(buffer, format='PNG', optimize=True)
        png_data = buffer.getvalue()

        # 构建图标条目: 类型(4) + 长度(4) + 数据
        # 长度 = 类型(4) + 长度字段(4) + 数据长度
        entry_length = 4 + 4 + len(png_data)
        entry = icon_type + struct.pack('>I', entry_length) + png_data

        icon_data_list.append(entry)

    # 构建 icns 文件头
    # icns 头部: 'icns' (4) + 文件总长度(4) + 所有图标条目
    total_length = 4 + 4 + sum(len(entry) for entry in icon_data_list)
    header = b'icns' + struct.pack('>I', total_length)

    # 写入文件
    with open(output_path, 'wb') as f:
        f.write(header)
        for entry in icon_data_list:
            f.write(entry)

    print(f"[OK] 已生成: {output_path}")


def create_png_icons(icon_path, output_dir):
    """
    创建各种尺寸的 PNG 图标
    """
    source = Image.open(icon_path)

    # 对于 ICO 文件，Pillow 会自动选择最大尺寸

    # 转换为 RGBA
    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    # 生成各种尺寸
    sizes = [32, 128, 256]

    for size in sizes:
        resized = source.resize((size, size), Image.LANCZOS)

        if size == 128:
            # 生成普通和 @2x 版本
            output_path = os.path.join(output_dir, f'128x128.png')
            resized.save(output_path, 'PNG', optimize=True)
            print(f"[OK] 已生成: {output_path}")

            # @2x 版本 (256x256)
            resized_2x = source.resize((256, 256), Image.LANCZOS)
            output_path_2x = os.path.join(output_dir, '128x128@2x.png')
            resized_2x.save(output_path_2x, 'PNG', optimize=True)
            print(f"[OK] 已生成: {output_path_2x}")
        else:
            output_path = os.path.join(output_dir, f'{size}x{size}.png')
            resized.save(output_path, 'PNG', optimize=True)
            print(f"[OK] 已生成: {output_path}")


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 项目根目录 (icons 目录在 src-tauri 下，所以需要向上两级)
    project_root = os.path.dirname(os.path.dirname(script_dir))
    src_dir = os.path.join(project_root, 'src')

    # 源图标路径 - 使用绝对路径
    source_icon = os.path.abspath(os.path.join(src_dir, 'icon.ico'))

    if not os.path.exists(source_icon):
        print(f"错误: 源图标不存在: {source_icon}")
        print("请确保 src/icon.ico 文件存在")
        sys.exit(1)

    print(f"使用源图标: {source_icon}")
    print("=" * 50)

    try:
        # 生成 PNG 图标
        print("\n生成 PNG 图标...")
        create_png_icons(source_icon, script_dir)

        # 生成 icns 文件
        print("\n生成 macOS icns 图标...")
        icns_path = os.path.join(script_dir, 'icon.icns')
        create_icns(source_icon, icns_path)

        print("\n" + "=" * 50)
        print("[OK] 所有图标生成完成!")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
