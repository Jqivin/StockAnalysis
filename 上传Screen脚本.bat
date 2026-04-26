@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 上传Screen管理脚本到服务器
echo 服务器: 60.205.188.111 (root用户)
echo ========================================
echo.

set SERVER_IP=60.205.188.111
set SERVER_USER=root
set LOCAL_DIR=%~dp0

echo 本地目录: %LOCAL_DIR%
echo 服务器: %SERVER_USER%@%SERVER_IP%
echo.

echo ========================================
echo 正在上传Screen管理脚本...
echo ========================================
echo.

REM 上传所有screen相关脚本
echo "1. 上传 run_with_screen.sh..."
scp "%LOCAL_DIR%run_with_screen.sh" %SERVER_USER%@%SERVER_IP%:/root/stock/

echo "2. 上传 stop_with_screen.sh..."
scp "%LOCAL_DIR%stop_with_screen.sh" %SERVER_USER%@%SERVER_IP%:/root/stock/

echo "3. 上传 view_logs.sh..."
scp "%LOCAL_DIR%view_logs.sh" %SERVER_USER%@%SERVER_IP%:/root/stock/

echo "4. 上传 check_status.sh..."
scp "%LOCAL_DIR%check_status.sh" %SERVER_USER%@%SERVER_IP%:/root/stock/

echo.
echo ========================================
echo ✅ 上传完成！
echo ========================================
echo.
echo 下一步操作（在服务器上执行）:
echo.
echo 1. 登录服务器:
echo    ssh root@%SERVER_IP%
echo.
echo 2. 进入目录并设置权限:
echo    cd /root/stock
echo    chmod +x run_with_screen.sh stop_with_screen.sh view_logs.sh check_status.sh
echo.
echo 3. 启动程序:
echo    ./run_with_screen.sh
echo.
echo 4. 查看状态:
echo    ./check_status.sh
echo.
echo ========================================
echo.

pause
