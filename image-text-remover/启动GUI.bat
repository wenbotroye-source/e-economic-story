@echo off
chcp 65001 >nul
echo ==========================================
echo     图包去文字工具 - GUI版
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python
    pause
    exit
)

REM 运行GUI
echo 正在启动图形界面...
python gui_app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查：
    echo   1. 是否已安装依赖：pip install -r requirements.txt
    echo   2. 配置文件是否正确
    pause
)
