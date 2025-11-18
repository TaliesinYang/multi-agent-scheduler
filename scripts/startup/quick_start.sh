#!/bin/bash

# Multi-Agent Scheduler - Quick Start Script
# 快速启动脚本（适用于Linux/Mac）

echo "=========================================="
echo "  Multi-Agent Scheduler - Quick Start"
echo "=========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python版本: $python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo ""
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "安装依赖包..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ 依赖安装完成"

# 运行Demo
echo ""
echo "=========================================="
echo "  启动Demo程序"
echo "=========================================="
echo ""
python demo.py

deactivate
