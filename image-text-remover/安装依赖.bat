@echo off
chcp 65001 >nul
echo ==========================================
echo     安装Python依赖包
echo ==========================================
echo.

REM 尝试使用不同的Python路径
set PYTHON_PATHS=(
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Users\Troye Chen\AppData\Local\Microsoft\WindowsApps\python.exe"
    python
)

for %%p in (%PYTHON_PATHS%) do (
    echo 尝试使用: %%p
    %%p --version >nul 2>&1
    if not errorlevel 1 (
        echo [OK] 找到Python: %%p
        set PYTHON=%%p
        goto :found_python
    )
)

echo [错误] 未找到可用的Python安装
pause
exit

:found_python
echo.
echo 使用Python: %PYTHON%
echo 安装依赖包...

%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt

if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit
)

echo.
echo [成功] 依赖安装完成!
echo.
echo 现在可以运行: 启动GUI.bat
pause