@echo off
chcp 65001 >nul
echo ==========================================
echo     图包去文字工具 - GUI版
echo ==========================================
echo.

REM 设置Python路径
set PYTHON_PATH=C:\Program Files\Python312\python.exe

REM 检查Python
echo 检查Python安装...
if not exist "%PYTHON_PATH%" (
    echo [错误] 未找到Python，请检查安装路径: %PYTHON_PATH%
    pause
    exit
)

echo [OK] 找到Python: %PYTHON_PATH%

REM 检查Python版本
"%PYTHON_PATH%" --version
if errorlevel 1 (
    echo [错误] Python版本检查失败
    pause
    exit
)

REM 运行GUI
echo.
echo 正在启动图形界面...
"%PYTHON_PATH%" gui_app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查：
    echo   1. 是否已安装依赖："%PYTHON_PATH%" -m pip install -r requirements.txt
    echo   2. 配置文件是否正确
    pause
)