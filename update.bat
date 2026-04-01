@echo off
echo ========================================
echo 修复 Telegram 账号收购机器人
echo ========================================
echo.

cd E:\工具\tgbot\tgacc

echo [1/5] 备份配置文件...
if exist .env (
    copy /Y .env ..\env_backup.txt >nul
    echo   ✓ 配置文件已备份
) else (
    echo   ! 未找到配置文件
)

echo.
echo [2/5] 删除旧代码...
cd ..
rmdir /s /q tgacc >nul 2>&1
echo   ✓ 旧代码已删除

echo.
echo [3/5] 克隆最新代码...
git clone https://github.com/ochoatanny845-ops/tg-account-buyer.git tgacc
if errorlevel 1 (
    echo   ✗ 克隆失败
    pause
    exit /b 1
)
echo   ✓ 最新代码已下载

echo.
echo [4/5] 恢复配置文件...
if exist env_backup.txt (
    move /Y env_backup.txt tgacc\.env >nul
    echo   ✓ 配置文件已恢复
) else (
    echo   ! 未找到备份文件
)

echo.
echo [5/5] 安装依赖...
cd tgacc
pip install -r requirements.txt
if errorlevel 1 (
    echo   ✗ 依赖安装失败
    pause
    exit /b 1
)
echo   ✓ 依赖已安装

echo.
echo ========================================
echo 更新完成！
echo ========================================
echo.
echo 现在可以运行: python main.py
echo.
pause
