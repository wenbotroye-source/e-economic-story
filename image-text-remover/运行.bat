@echo off
chcp 65001 >nul
echo ==========================================
echo     图包去文字工具
echo ==========================================
echo.

REM 检查输入目录
if not exist "input" (
    mkdir input
    echo [提示] 已创建 input 文件夹，请放入图片后重新运行
    pause
    exit
)

REM 运行程序
python main.py -i ./input -o ./output

echo.
pause
