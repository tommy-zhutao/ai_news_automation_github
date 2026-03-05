@echo off
echo ================================================
echo   AI新闻自动化系统 - Web管理界面
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查是否安装了Flask
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 检测到Flask未安装，正在安装依赖...
    pip install Flask Flask-SQLAlchemy
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo [启动] 正在启动Web服务器...
echo [访问] 访问地址: http://localhost:5000
echo [提示] 按 Ctrl+C 停止服务器
echo.

REM 启动Web服务器
python run_web.py --host 0.0.0.0 --port 5000

pause
