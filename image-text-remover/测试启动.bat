@echo off
chcp 65001 >nul
echo ==========================================
echo     图包去文字工具 - 测试启动
echo ==========================================
echo.

REM 设置Python路径
set PYTHON_PATH=C:\Program Files\Python312\python.exe

echo 1. 检查Python安装...
if not exist "%PYTHON_PATH%" (
    echo [错误] 未找到Python: %PYTHON_PATH%
    pause
    exit
)
echo [OK] Python found: %PYTHON_PATH%

echo.
echo 2. 检查Python版本...
"%PYTHON_PATH%" --version

echo.
echo 3. 测试导入核心模块...
"%PYTHON_PATH%" -c "from core.workflow import TextRemovalWorkflow; print('模块导入成功')"

if errorlevel 1 (
    echo [错误] 模块导入失败
    pause
    exit
)

echo.
echo 4. 测试初始化工作流...
"%PYTHON_PATH%" -c "from core.workflow import TextRemovalWorkflow; w = TextRemovalWorkflow(api_key='test_key', provider='nanobanana'); print('工作流初始化成功')"

if errorlevel 1 (
    echo [错误] 工作流初始化失败
    pause
    exit
)

echo.
echo ==========================================
echo [成功] 所有测试通过!
echo ==========================================
echo.
echo 现在可以运行: "%PYTHON_PATH%" gui_app.py
echo 或者双击: 启动工具_修复版.bat
pause