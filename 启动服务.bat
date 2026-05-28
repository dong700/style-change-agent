@echo off
chcp 65001 >nul
echo ========================================
echo   文章风格改写系统 - 启动中...
echo ========================================
echo.

REM 检查 conda 是否可用
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 conda，请确保已安装 Anaconda 并添加到 PATH
    pause
    exit /b 1
)

REM 激活环境
echo [1/3] 激活 Python 环境...
call conda activate style_ocr
if %errorlevel% neq 0 (
    echo [错误] 环境不存在，正在创建...
    call conda create -n style_ocr python=3.10 -y
    call conda activate style_ocr
)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查依赖
echo [2/3] 检查依赖...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [提示] 正在安装基础依赖...
    pip install Flask Werkzeug python-docx jieba PyPDF2 tqdm requests faiss-cpu -q
)

REM 启动服务
echo [3/3] 启动 Web 服务...
echo.
echo ========================================
echo   服务已启动！
echo   请在浏览器访问: http://localhost:5000
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

python web_app/app.py

pause
