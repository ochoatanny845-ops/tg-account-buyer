@echo off
echo ========================================
echo 代码提交前检查
echo ========================================
echo.

echo [1/2] 运行代码质量检查...
python check_code.py
if errorlevel 1 (
    echo.
    echo ❌ 代码检查失败！请修复上述问题后再提交。
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] 检查已删除的函数调用...
findstr /s /i /c:"login_with_code" *.py bot\*.py bot\handlers\*.py bot\utils\*.py >nul 2>&1
if not errorlevel 1 (
    echo ❌ 发现已删除的函数 login_with_code 的调用
    echo.
    pause
    exit /b 1
)
echo ✅ 无已删除函数调用

echo.
echo ========================================
echo ✅ 所有检查通过！可以安全提交。
echo ========================================
echo.
pause
