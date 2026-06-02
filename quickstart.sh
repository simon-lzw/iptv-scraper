#!/usr/bin/env bash
#
# IPTV Scraper - Quick Start (Linux/Mac)
# 用法: bash <(curl -s https://raw.githubusercontent.com/你的用户名/iptv-scraper/main/quickstart.sh)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   IPTV 直播源自动搜刮系统 - 安装     ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# 检测 Python
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        PYTHON=$cmd
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ 未找到 Python，请先安装 Python 3.8+${NC}"
    exit 1
fi

PY_VER=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
echo -e "${GREEN}✅ 检测到 Python ${PY_VER}${NC}"

# 检测 Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ 未找到 Git，请先安装 Git${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 检测到 Git${NC}"

# 检测是否在项目目录中
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 克隆项目...${NC}"
    git clone --depth 1 https://github.com/Shra1V32/iptv-scraper.git 2>/dev/null || \
    git clone --depth 1 https://github.com/你的用户名/iptv-scraper.git
    cd iptv-scraper
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    $PYTHON -m venv venv
fi

source venv/bin/activate

# 安装依赖
echo -e "${YELLOW}📦 安装依赖...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo -e "${GREEN}✅ 依赖安装完成${NC}"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗"
echo "║   安装完成！请选择启动方式            ║"
echo "╚══════════════════════════════════════╝${NC}"
echo ""
echo "  ${GREEN}1)${NC} 完整启动（搜刮 + HTTP 服务 + 调度）"
echo "     python main.py"
echo ""
echo "  ${GREEN}2)${NC} 仅 HTTP 服务（已有数据时）"
echo "     python main.py --server"
echo ""
echo "  ${GREEN}3)${NC} 交互式管理菜单"
echo "     python main.py --menu"
echo ""
echo "  📺 播放器添加: http://localhost:5000/playlist.m3u"
echo ""
