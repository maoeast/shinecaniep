@echo off
chcp 65001 >nul 2>&1 || chcp 936 >nul
cd /d "%~dp0"

echo ==========================================
echo   Resource Room Management System - IEP
echo ==========================================
echo.

echo Current directory: %cd%
echo.

set "TAURI_EXE=%cd%\src-tauri\target\release\shinecaniep.exe"
echo Executable path: %TAURI_EXE%
echo.

if not exist "%TAURI_EXE%" (
    echo [Error] Tauri executable not found at:
    echo %TAURI_EXE%
    pause
    exit /b 1
)

echo Checking dist folder...
if exist "dist\index.html" (
    echo dist/index.html found
) else (
    echo [Warning] dist/index.html not found
)
echo.

echo Starting application...
echo.
"%TAURI_EXE%"

if errorlevel 1 (
    echo.
    echo [Error] Application exited with code %errorlevel%
    pause
)
