@echo off
REM IPTV Scraper 启动脚本 (Windows)
REM 设置 UTF-8 编码避免 emoji 打印乱码
set PYTHONIOENCODING=utf-8
python main.py %*
