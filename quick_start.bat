@echo off
REM Multi-Agent Scheduler - Quick Start Script
REM 快速启动脚本（Windows）

echo ==========================================
echo   Multi-Agent Scheduler - Quick Start
echo ==========================================

REM 检查Python
python --version
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo ✓ Python已安装

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo.
    echo 正在创建虚拟环境...
    python -m venv venv
    echo ✓ 虚拟环境创建成功
)

REM 激活虚拟环境
echo.
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 安装依赖包...
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo ✓ 依赖安装完成

REM 运行Demo
echo.
echo ==========================================
echo   启动Demo程序
echo ==========================================
echo.
python demo.py

deactivate
pause
