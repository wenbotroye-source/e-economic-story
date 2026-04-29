@echo off
chcp 65001 >nul
echo ==========================================
echo     图包去文字工具 - 通用模式
echo ==========================================
echo.

if not exist "input" (
    mkdir input
    echo [提示] 已创建 input 文件夹，请放入图片后重新运行
    pause
    exit
)

python main.py -i ./input -o ./output --scene universal

echo.
pause
