@echo off
chcp 65001 >nul
echo ========================================
echo   项目打包工具
echo ========================================
echo.

REM 获取当前目录
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM 获取父目录
for %%I in ("%PROJECT_DIR%") do set "PARENT_DIR=%%~dpI"

REM 设置输出路径
set "TEMP_DIR=%PARENT_DIR%temp_package"
set "ZIP_FILE=%PARENT_DIR%文章风格改写系统.zip"

echo 项目目录: %PROJECT_DIR%
echo 输出文件: %ZIP_FILE%
echo.

REM 清理旧的临时目录
if exist "%TEMP_DIR%" (
    echo [1/6] 清理临时目录...
    rmdir /s /q "%TEMP_DIR%"
)

REM 创建临时目录
echo [2/6] 创建临时目录...
mkdir "%TEMP_DIR%"

REM 复制核心文件
echo [3/6] 复制核心文件...
xcopy "%PROJECT_DIR%\web_app" "%TEMP_DIR%\web_app" /E /I /Q
xcopy "%PROJECT_DIR%\large_text_processor" "%TEMP_DIR%\large_text_processor" /E /I /Q
xcopy "%PROJECT_DIR%\templates" "%TEMP_DIR%\templates" /E /I /Q
copy "%PROJECT_DIR%\style_extractor.py" "%TEMP_DIR%\" /Y
copy "%PROJECT_DIR%\style_rewriter.py" "%TEMP_DIR%\" /Y
copy "%PROJECT_DIR%\requirements.txt" "%TEMP_DIR%\" /Y
copy "%PROJECT_DIR%\requirements_ocr.txt" "%TEMP_DIR%\" /Y
copy "%PROJECT_DIR%\使用说明.md" "%TEMP_DIR%\" /Y
copy "%PROJECT_DIR%\启动服务.bat" "%TEMP_DIR%\" /Y

REM 创建空目录
echo [4/6] 创建缓存目录...
mkdir "%TEMP_DIR%\cache"
mkdir "%TEMP_DIR%\output"

REM 删除旧的压缩包
if exist "%ZIP_FILE%" (
    echo [5/6] 删除旧的压缩包...
    del "%ZIP_FILE%"
)

REM 使用 PowerShell 打包
echo [6/6] 创建压缩包...
powershell -Command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%ZIP_FILE%' -CompressionLevel Optimal"

REM 清理临时目录
echo.
echo 清理临时文件...
rmdir /s /q "%TEMP_DIR%"

echo.
echo ========================================
echo   打包完成！
echo   文件位置: %ZIP_FILE%
echo ========================================
echo.

pause
