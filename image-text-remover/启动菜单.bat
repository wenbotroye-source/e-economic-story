@echo off
chcp 65001 >nul

:menu
cls
echo ==========================================
echo     图包去文字工具 - 启动菜单
echo ==========================================
echo.
echo  [1] 自动模式 - 智能识别图片类型
echo  [2] 通用模式 - 使用统一Prompt
echo  [3] 白底产品图 - 纯白背景
echo  [4] 场景图模式 - 生活方式图
echo  [5] 服装模特模式
echo  [6] 食品美食模式
echo  [7] 3C电子模式
echo.
echo  [0] 退出
echo.
echo ==========================================
set /p choice=请选择模式 (0-7):

if "%choice%"=="1" goto auto
if "%choice%"=="2" goto universal
if "%choice%"=="3" goto white
if "%choice%"=="4" goto lifestyle
if "%choice%"=="5" goto fashion
if "%choice%"=="6" goto food
if "%choice%"=="7" goto electronics
if "%choice%"=="0" exit
goto menu

:auto
call :run auto
pause
goto menu

:universal
call :run universal
pause
goto menu

:white
call :run white_background
pause
goto menu

:lifestyle
call :run lifestyle
pause
goto menu

:fashion
call :run fashion
pause
goto menu

:food
call :run food
pause
goto menu

:electronics
call :run electronics
pause
goto menu

:run
if not exist "input" (
    mkdir input
    echo [提示] 已创建 input 文件夹，请放入图片后重新运行
    exit /b
)
echo.
echo [运行模式: %~1]
echo ------------------------------------------
python main.py -i ./input -o ./output --scene %~1
echo ------------------------------------------
exit /b
