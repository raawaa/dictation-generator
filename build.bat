@echo off
chcp 65001 >nul
echo ========================================
echo 英语单词默写纸生成器 - 打包脚本
echo ========================================

echo.
echo [1/4] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [2/4] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装Python或激活conda环境
    pause
    exit /b 1
)

echo.
echo [3/4] 检查依赖...
python -c "import PyQt6; import reportlab; import pyinstaller"
if %errorlevel% neq 0 (
    echo 警告：部分依赖未安装，尝试安装...
    pip install PyQt6 reportlab pyinstaller
)

echo.
echo [4/4] 执行打包...
pyinstaller build.spec
if %errorlevel% neq 0 (
    echo 错误：打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo 输出文件: dist\英语单词默写纸生成器.exe
echo ========================================

pause