# 图标说明

Tauri 需要以下格式的图标文件：

- `32x32.png` - Windows 任务栏图标
- `128x128.png` - Linux 应用程序图标
- `128x128@2x.png` - macOS Retina 显示屏图标
- `icon.icns` - macOS 应用程序图标
- `icon.ico` - Windows 应用程序图标

## 生成图标

### 方法1：使用 Tauri 图标生成器

如果你有一张 1024x1024 的源图片：

```bash
# 安装 Tauri 图标生成工具
cargo install tauri-icon

# 生成所有图标
# 替换 path/to/your/icon.png 为你的源图片路径
tauri-icon path/to/your/icon.png
```

### 方法2：使用在线工具

1. 访问 https://tauri.app/v1/guides/features/icons/
2. 或使用 https://www.icoconverter.com/ 生成 .ico
3. 使用 https://cloudconvert.com/png-to-icns 生成 .icns

### 方法3：使用 ImageMagick

```bash
# 生成 PNG 图标
convert icon.png -resize 32x32 32x32.png
convert icon.png -resize 128x128 128x128.png
convert icon.png -resize 256x256 128x128@2x.png

# 生成 ICO 文件 (多尺寸)
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico

# 生成 ICNS 文件 (macOS)
# macOS 上使用 iconutil 工具
```

## 源图标位置

项目已有的图标位于：
- `/home/DONG/Mycode/shinecaniep/src/icon.ico`

建议使用这个文件作为源文件生成其他格式。
