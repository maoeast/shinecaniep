@echo off
chcp 65001 >nul
echo ==========================================
echo   资源教室管理系统-IEP (Tauri 桌面版)
echo ==========================================
echo.

set "TAURI_EXE=%~dp0src-tauri\target\release\shinecaniep.exe"

if not exist "%TAURI_EXE%" (
    echo [错误] 未找到 Tauri 可执行文件
    echo 请先构建项目：
    echo   cd src-tauri
    echo   cargo build --release
    pause
    exit /b 1
)

echo 正在启动应用...
"%TAURI_EXE%"

if errorlevel 1 (
    echo.
    echo [错误] 应用启动失败
    pause
)
