# IPTV 直播源自动搜刮系统

> 自动搜刮、健康检查、失效自动替换的 IPTV 直播源管理工具  
> 覆盖 **中国大陆 / 香港 / 澳门 / 台湾** 共 **2334+ 个频道**  
> 受 [Playlist-AutoUpdater](https://github.com/Shra1V32/Playlist-AutoUpdater) 和 [Tata-Sky-IPTV](https://github.com/ForceGT/Tata-Sky-IPTV) 启发设计

---

## 目录

- [快速开始](#快速开始)
- [频道覆盖](#频道覆盖)
- [系统架构](#系统架构)
- [部署方式](#部署方式)
- [使用方法](#使用方法)
- [API 参考](#api-参考)
- [配置指南](#配置指南)
- [自动修复机制](#自动修复机制)
- [搜刮源说明](#搜刮源说明)
- [项目对比](#项目对比)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 快速开始

### 方式 A：零成本部署（推荐）

利用 GitHub Actions 免费额度，无需自建服务器：

```bash
# 1. Fork 本仓库
# 2. 进入你的仓库 → Actions → 启用 GitHub Actions
# 3. 等待首次自动运行（或手动触发）
```

播放列表自动更新到（两种分组方式）：

```
# 标准版：按区域 → 分组排序
https://raw.githubusercontent.com/<你的用户名>/iptv-scraper/main/data/playlist.m3u

# 协议版：按 IPv6(148) / IPv4(2096) / RTP(90) 分组
https://raw.githubusercontent.com/<你的用户名>/iptv-scraper/main/data/playlist_by_protocol.m3u
```

将上述 URL 添加到电视播放器即可。**每天自动更新，电脑无需开机，全球 CDN 加速。**

### 方式 B：本地运行

需要 Web 管理界面时使用：

```bash
# 一键安装 (Linux/Mac)
bash <(curl -s https://raw.githubusercontent.com/你的用户名/iptv-scraper/main/quickstart.sh)

# 或手动安装
cd iptv-scraper
pip install -r requirements.txt

# 完整启动（搜刮 + HTTP 服务 + 定时调度）
python main.py

# 或仅 HTTP 服务（已有数据时）
python main.py --server
```

电视播放器添加（两种分组）：

```
http://<你的IP>:5000/playlist.m3u               # 标准版
http://<你的IP>:5000/playlist_by_protocol.m3u   # 协议版
```

### 方式 C：Docker（即将推出）

```bash
# TODO: Docker 镜像支持
```

---

## 频道覆盖

| 区域 | 数量 | 主要频道 |
|------|------|---------|
| 📡 **中国大陆** | **2157** | CCTV-1~17、CGTN、各省级卫视、地方频道、数字频道、电影频道、体育频道 |
| 🇭🇰 **香港** | **60** | 翡翠台(TVB Jade)、明珠台(TVB Pearl)、无线新闻(TVB News)、无线财经、无线星河、J2、ViuTV、HOY TV、凤凰卫视/中文/资讯/香港、RTHK 31~35、TVBS亚洲、香港卫视 |
| 🇲🇴 **澳门** | **7** | TDM 澳视澳门、TDM 资讯、TDM 体育、TDM 综艺、TDM Entertainment、Canal Macau |
| 🇹🇼 **台湾** | **80** | 台视(含新闻)、三立台湾/新闻、东森(6个)、纬来(3个)、靖天(3个)、中天(4个)、华视新闻、民视、TVBS、寰宇新闻 |
| **总计** | **2304** | 相比之前 +466 个频道 |

> 频道数量因搜刮源变化可能波动，系统每天自动更新。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    iptv-scraper 系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  搜刮层 (scrapers/)                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ GitHubScraper    WebScraper                        │    │
│  │ - fanmingming    - iptvcat (可扩展)                │    │
│  │ - YueChan/Live                                     │    │
│  │ - iptv-org (cn/hk/mo/tw)                           │    │
│  │ - Guovin/iptv-api                                  │    │
│  └──────────┬─────────────────────────────────────────┘    │
│             ↓                                               │
│  存储层 (db.py)                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ SQLite + WAL 模式                                   │    │
│  │ channels 表: name, url, region, kodi_props, ...    │    │
│  │ scrape_records 表: 搜刮历史日志                      │    │
│  └──────────┬─────────────────────────────────────────┘    │
│             ↓                                               │
│  校验层 (checker.py)                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ HTTP HEAD 并发检查 (aiohttp, 20并发)               │    │
│  │ 连续3次失败 → 标记 inactive                         │    │
│  │ 深度检查 (30s超时, 用于失效频道恢复验证)              │    │
│  └──────────┬─────────────────────────────────────────┘    │
│             ↓                                               │
│  输出层 (m3u_generator.py)                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 按 区域 → 分组 → 名称 排序                          │    │
│  │ 输出标准 M3U 格式                                   │    │
│  │ 保留 KODIPROP DRM 许可证信息                        │    │
│  └──────────┬─────────────────────────────────────────┘    │
│             ↓                                               │
│  服务层 (server.py)                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Flask HTTP: playlist.m3u + REST API + Web UI      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  调度层 (schedule)                                           │
│  ├── 全量搜刮: 每 6 小时                                    │
│  ├── 健康检查: 每 30 分钟                                   │
│  └── 自动修复: 每 15 分钟                                   │
│                                                             │
│  管理界面                                                   │
│  ├── Web UI (http://<IP>:5000/)                             │
│  └── CLI 菜单 (python main.py --menu)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
公开 M3U 源 (GitHub)
     ↓ 爬取 + 解析
原始频道数据 (name, url, group, region, kodi_props)
     ↓ 去重 + 分类
SQLite 数据库 (channels.db)
     ↓ 查询活跃频道
M3U 生成器
     ↓
playlist.m3u          (标准版：按区域→分组)
playlist_by_protocol.m3u  (协议版：按 IPv6/IPv4/RTP)
     ↓ HTTP 提供
电视播放器 (TiviMate / VLC / Kodi)
```

---

## 部署方式

### 1. GitHub Actions（推荐）

适合不想维护服务器的用户。

| 特性 | 说明 |
|------|------|
| 成本 | **免费**（GitHub 免费额度每月 2000 分钟） |
| 更新频率 | 每天 2 次（北京时间 10:00 / 22:00） |
| 稳定性 | 全球 CDN 加速，GitHub 高可用 |
| 局限性 | 无 Web 管理界面，无法实时健康检查 |

**步骤：**
1. Fork 本仓库
2. 进入仓库 → **Actions** → 启用 workflows
3. 手动触发一次 `自动搜刮直播源` workflow
4. 等待运行完成
5. 电视播放器添加：`https://raw.githubusercontent.com/<你的用户名>/iptv-scraper/main/data/playlist.m3u`

**CI 缓存：** 数据库文件通过 `actions/cache` 持久化，跨运行保持频道失效计数。

### 2. Gitee Go

Gitee 仓库使用 `.workflow/master-pipeline.yml` 执行相同的自动搜刮流程。Gitee Go 会以 detached HEAD 检出代码，因此流水线在提交后使用 `git push origin HEAD:main` 明确更新远端 `main` 分支，不能依赖无参数的 `git push`。

### 3. 本地服务器

适合需要实时管理、Web 界面的用户。

```bash
# 方式 A：完整启动（推荐）
python main.py

# 方式 B：仅 HTTP 服务（已有数据时）
python main.py --server

# 方式 C：仅执行一次搜刮
python main.py --scrape

# 方式 D：仅执行健康检查
python main.py --check

# 方式 E：深度检查失效频道（30s 超时）
python main.py --deep-check

# 方式 F：交互式管理菜单
python main.py --menu

# 方式 G：带日志文件
python main.py --log-file debug.log
```

---

## 使用方法

### 电视播放器设置

| 平台 | 推荐播放器 | 说明 |
|------|-----------|------|
| **Android TV** | [TiviMate](https://tivimate.com/) | 最佳体验，支持自动刷新、EPG、收藏 |
| **Android TV / 手机** | [IPTV Smarters](https://www.iptvsmarters.com/) | 界面友好 |
| **iOS / Apple TV** | [iPlayTV](https://apps.apple.com/us/app/iplaytv/id1476362770) | 稳定流畅 |
| **iOS / Apple TV** | [GSE SMART IPTV](https://apps.apple.com/us/app/gse-smart-iptv/id1028734027) | 功能丰富 |
| **全平台** | [VLC Media Player](https://www.videolan.org/) | 免费开源 |
| **全平台** | [Kodi](https://kodi.tv/) + PVR IPTV Simple Client | 高度可定制 |
| **Windows** | [PotPlayer](https://potplayer.tv/) | 硬件加速好 |

### Web 管理界面

启动 HTTP 服务后，浏览器访问：

```
http://<你的IP>:5000/
```

功能：
- 查看系统状态（总频道 / 活跃 / 失效）
- 查看播放列表地址
- 手动触发搜刮
- 手动触发修复
- 频道列表页面

### CLI 交互菜单

```bash
python main.py --menu
```

```
==================================================
  📺 IPTV 直播源管理系统
==================================================

  📊 当前状态: 1838 频道 | 1838 活跃 | 0 失效

  ┌─────────────────────────────────────┐
  │ 1. 📊 查看详细状态                   │
  │ 2. 🔍 执行搜刮                       │
  │ 3. 📺 查看频道列表                   │
  │ 4. ❌ 查看失效频道                   │
  │ 5. 🔧 修复失效频道                   │
  │ 6. 🏥 健康检查                       │
  │ d. 🔍 深度检查(失效频道恢复)          │
  │ 7. 🚪 退出                           │
  └─────────────────────────────────────┘
```

---

## API 参考

HTTP 服务启动后可用（默认 `http://0.0.0.0:5000`）。

### 播放列表

```
# 标准版：按区域 → 分组 → 名称排序
GET /playlist.m3u

# 协议版：按 IPv6 / IPv4 / RTP → 区域排序
GET /playlist_by_protocol.m3u
```

**响应头：** `Content-Type: application/x-mpegurl`

### 系统状态

```
GET /api/status
```

```json
{
  "status": "running",
  "channels": {
    "total": 1838,
    "active": 1838,
    "inactive": 0
  }
}
```

### 频道列表

```
GET /api/channels
GET /api/channels?region=hongkong
GET /api/channels?region=taiwan
```

参数 `region` 可选值：`mainland`, `hongkong`, `macau`, `taiwan`

### 失效频道

```
GET /api/channels/inactive
```

返回所有连续失败 3 次以上被标记为失效的频道。

### 手动操作

```
POST /api/scrape    # 触发搜刮
POST /api/heal      # 触发修复
```

---

## 配置指南

编辑 `config.py` 可自定义：

### 基本设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | HTTP 服务监听地址 |
| `PORT` | `5000` | HTTP 服务端口 |
| `HEALTH_CHECK_INTERVAL_MINUTES` | `30` | 健康检查间隔（分钟） |
| `SCRAPE_INTERVAL_HOURS` | `6` | 全量搜刮间隔（小时） |
| `AUTO_HEAL_INTERVAL_MINUTES` | `15` | 自动修复间隔（分钟） |

### 健康检查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `HEALTH_CHECK_TIMEOUT_SECONDS` | `8` | 单源超时（秒） |
| `MAX_FAIL_COUNT` | `3` | 连续失败次数阈值 |
| `MAX_CONCURRENT_CHECKS` | `20` | 并发检查数 |

### 搜刮源

`GITHUB_M3U_SOURCES` 列表定义了所有搜刮源。当前包含 7 个源：

```python
GITHUB_M3U_SOURCES = [
    # 大陆 IPV6 源
    {"name": "fanmingming/live (ipv6)", "url": "...", "region": "cn"},
    # 北京联通 IPTV
    {"name": "YueChan/Live", "url": "...", "region": "cn"},
    # iptv-org 国际源
    {"name": "iptv-org China", "url": "...", "region": "cn"},
    {"name": "iptv-org Hong Kong", "url": "...", "region": "hk"},
    {"name": "iptv-org Macau", "url": "...", "region": "macau"},
    {"name": "iptv-org Taiwan", "url": "...", "region": "tw"},
    # 综合大源 (含完整港澳台分组)
    {"name": "Guovin/iptv-api (ipv6)", "url": "...", "region": "all"},
]
```

可以自由添加/删除源。`region` 字段控制频道分类：
- `cn` → 中国大陆
- `hk` → 香港
- `macau` / `mo` → 澳门
- `tw` → 台湾
- `all` → 自动分类（依赖分类器）

---

## 自动修复机制

系统内置三层次自动修复：

### 第一层：健康检查（每 30 分钟）

```
全部活跃频道 → HTTP HEAD 并发检查 (20并发)
    ↓
响应 < 8s 且 HTTP 200 → 成功计数 +1
    ↓ 失败
失败计数 +1
    ↓ 连续失败 ≥ 3 次
标记为 inactive，从播放列表中移除
    ↓
重新生成 M3U（排除失效源）
```

### 第二层：自动修复（每 15 分钟）

```
扫描所有 inactive 频道
    ↓
对每个失效频道：
    1. 查找数据库中是否有同名的其他活跃源
    2. 如果没有，用所有搜刮器重新搜索该频道名
    ↓
找到新源 → 替换 URL，重置失败计数，重新激活
    ↓
找不到 → 记录失败，等待下次修复
```

### 第三层：深度检查（手动触发）

```
python main.py --deep-check
```

对 inactive 频道使用 **30 秒超时**（而非默认 8 秒）逐个测试，避免因网络波动误判。恢复的频道自动重新激活。

---

## 搜刮源说明

| 源 | 类型 | 频道数 | 特点 |
|---|------|--------|------|
| **fanmingming/live** | IPv6 | ~82 | 央视 + 卫视，需要 IPv6 网络 |
| **YueChan/Live** | 北京联通 IPTV | ~90 | RTP 组播源 |
| **iptv-org Hong Kong** | 全球聚合 | ~13 | 凤凰卫视、RTHK、HOY |
| **iptv-org Macau** | 全球聚合 | ~6 | TDM 各频道 |
| **iptv-org Taiwan** | 全球聚合 | ~22 | 台视、华视、三立、东森 |
| **Guovin/iptv-api** (升级↑) | 综合(IPv4+IPv6) | **~1722** | **核心源**，含完整港澳台分组 |
| **vbskycn/iptv** (新增✨) | 大陆地方频道 | **~349** | 补充地方台/数字台/电影频道 |
| **zhi35** (新增✨) | 每日聚合镜像 | ~20+ | 港澳台补充源，每日更新 |

> 去重后总计 **2304** 个唯一频道。iptv-org China 源已失效 (2026-06)，注释保留备用。

---

## 项目对比

本项目参考了以下两个知名项目：

| 特性 | [Playlist-AutoUpdater](https://github.com/Shra1V32/Playlist-AutoUpdater) | [Tata-Sky-IPTV](https://github.com/ForceGT/Tata-Sky-IPTV) | 本系统 |
|------|-----------------------------------------------------------------------|-----------------------------------------------------------|--------|
| **状态** | 🧟 已归档/EOL | 🟡 低维护 | ✅ 活跃 |
| **数据来源** | Tata Sky 认证 API | Tata Play API 逆向 | 公开 M3U 源聚合 |
| **覆盖区域** | 仅印度 | 仅印度 | 中国大陆/港澳台 |
| **技术栈** | Bash + Python | Python | Python asyncio |
| **需要订阅** | ✅ 需要 Tata Sky 账号 | ✅ 需要 Tata Play 账号 | ❌ 免费公开源 |
| **DRM 支持** | ❌ | ✅ 保留 Widevine 许可证 | ✅ KODIPROP 元数据保留 |
| **部署方式** | GitHub Actions + Gist | 本地脚本 | GitHub Actions / 本地 |
| **自动更新** | ✅ GitHub Actions 调度 | ❌ 手动每小时 | ✅ 多种调度策略 |
| **健康检查** | ❌ | ❌ | ✅ 30分钟自动检测 |
| **失效自动修复** | ❌ | ❌ | ✅ 15分钟自动替换 |
| **Web 管理** | ❌ | ❌ | ✅ Flask WebUI |
| **CLI 管理** | ✅ 终端菜单 | ❌ | ✅ --menu 交互模式 |
| **日志系统** | ❌ | ❌ | ✅ --log-file 轮转日志 |
| **一键安装** | ✅ curl \| bash | ❌ | ✅ quickstart.sh/ps1 |

### 本系统的独特优势

- **多源聚合**：7 个源同时搜刮，覆盖更全面
- **自动修复**：健康检查 + 失效替换，无需人工干预
- **多种部署**：GitHub Actions / 本地 / Docker（即将推出）
- **管理界面**：Web UI + API + CLI 三种管理方式
- **DRM 保留**：KODIPROP 许可证元数据完整传递
- **CI 缓存**：跨运行持久化数据库，失效计数不丢失

---

## 开发指南

### 环境要求

- Python 3.8+
- pip

### 本地开发

```bash
# 克隆
git clone https://github.com/你的用户名/iptv-scraper.git
cd iptv-scraper

# 安装依赖
pip install -r requirements.txt

# 测试导入
python -c "from db import Database; from main import IPTVScheduler; print('OK')"

# 测试搜刮（单个源）
python -c "
from scrapers.github_sources import GitHubScraper
s = GitHubScraper()
ch = s._scrape_single_source(s.sources[0])
print(f'Source: {s.sources[0][\"name\"]}, channels: {len(ch)}')
"
```

### 项目结构

```
iptv-scraper/
├── main.py                # 主入口：调度器 + 参数解析
├── config.py              # 所有可配置项
├── db.py                  # SQLite 数据库层（WAL 模式）
├── models.py              # 数据模型（Channel, M3UEntry）
├── m3u_generator.py       # M3U 播放列表生成器
├── checker.py             # 健康检查（aiohttp 并发）
├── server.py              # Flask HTTP 服务 + WebUI
├── logger.py              # 日志工具
├── cli_menu.py            # 交互式 CLI 菜单
├── scrapers/
│   ├── __init__.py
│   ├── base.py            # 爬虫基类（HTTP 重试、区域分类）
│   ├── github_sources.py  # GitHub M3U 源爬虫
│   └── web_sources.py     # 网页聚合站爬虫
├── .github/workflows/
│   └── scrape.yml         # GitHub Actions 自动部署
├── quickstart.sh          # Linux/Mac 一键安装
├── quickstart.ps1         # Windows 一键安装
├── data/
│   ├── channels.db               # SQLite 频道数据库
│   ├── playlist.m3u              # 标准播放列表 (区域→分组)
│   └── playlist_by_protocol.m3u  # 协议分组播放列表
└── requirements.txt
```

### 扩展指南

**添加新的搜刮源：**

1. 在 `config.py` 的 `GITHUB_M3U_SOURCES` 中添加新源
2. 或在 `scrapers/` 下创建新的爬虫类（继承 `BaseScraper`）
3. 在 `main.py` 的 `_init_scrapers()` 中注册

**添加新的区域分类：**

在 `scrapers/base.py` 的 `_classify_region()` 和 `config.py` 的 `GROUP_REGION_MAP` 中添加关键词。

---

## 常见问题

### 频道无法播放怎么办？

1. **健康检查会自动处理** — 系统每 30 分钟检测一次，连续 3 次失败自动标记失效
2. **自动修复** — 每 15 分钟尝试找替代源
3. **手动深度检查** — `python main.py --deep-check` 用 30 秒超时重新测试
4. **手动触发搜刮** — 通过 Web UI 或 `python main.py --scrape` 获取最新源

### GitHub Actions 部署后没有频道？

1. 进入仓库 → **Actions** → 检查 workflow 运行状态
2. 手动触发一次 `workflow_dispatch`
3. 等待运行完成（约 2-5 分钟）
4. 检查 `data/playlist.m3u` 是否已生成

### 如何添加自定义频道？

编辑 `config.py` 中的 `CHANNEL_OVERRIDES`，或直接在数据库中添加：

```python
from db import Database
from models import Channel
db = Database()
db.add_channel(Channel(
    name="自定义频道",
    url="http://your-stream-url.m3u8",
    group="自定义分组",
    region="mainland",
))
```

### 播放列表在 TiviMate 中不更新？

TiviMate 默认缓存播放列表。进入设置 → **播放列表** → 选择你的列表 → **更新**。

或设置自动更新：设置 → **播放列表** → **自动更新间隔** → 设为 6 小时。

### 为什么某些频道带 [Geo-blocked] 标签？

这些频道有地区限制，只在特定地区可用。系统保留了这些信息，你可以尝试使用代理或 VPN。

---

## 许可证

MIT License

Copyright (c) 2026

本项目仅供学习和研究使用。所有直播源来自公开的 IPTV 聚合项目，版权归各自所有者所有。
