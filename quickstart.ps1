# IPTV Scraper - Quick Start (Windows PowerShell)
# 用法: irm https://raw.githubusercontent.com/你的用户名/iptv-scraper/main/quickstart.ps1 | iex

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "IPTV Scraper - 安装"

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   IPTV 直播源自动搜刮系统 - 安装      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 检测 Python
$python = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $v = & $cmd --version 2>&1
        if ($v -match "Python 3\.(\d+)") {
            $python = $cmd
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "❌ 未找到 Python 3.8+，请先从 python.org 安装" -ForegroundColor Red
    exit 1
}

$pyVer = & $python --version
Write-Host "✅ 检测到 $pyVer" -ForegroundColor Green

# 检测 Git
try {
    $gitVer = git --version
    Write-Host "✅ 检测到 $gitVer" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Git，请先从 git-scm.com 安装" -ForegroundColor Red
    exit 1
}

# 检测是否在项目目录
if (-not (Test-Path "main.py") -or -not (Test-Path "requirements.txt")) {
    Write-Host "📦 克隆项目..." -ForegroundColor Yellow
    git clone --depth 1 https://github.com/你的用户名/iptv-scraper.git
    Set-Location iptv-scraper
}

# 创建虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    & $python -m venv venv
}

# 激活虚拟环境
if ($IsWindows -or $env:OS -match "Windows") {
    & .\venv\Scripts\Activate.ps1
} else {
    & ./venv/bin/Activate.ps1
}

# 安装依赖
Write-Host "📦 安装依赖..." -ForegroundColor Yellow
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

Write-Host "✅ 依赖安装完成！" -ForegroundColor Green
Write-Host ""

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   安装完成！请选择启动方式            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  python main.py          — 完整启动（搜刮+HTTP+调度）" -ForegroundColor Green
Write-Host "  python main.py --server — 仅 HTTP 服务" -ForegroundColor Green
Write-Host "  python main.py --menu   — 交互式管理菜单" -ForegroundColor Green
Write-Host ""
Write-Host "  📺 播放器添加: http://localhost:5000/playlist.m3u" -ForegroundColor Cyan
