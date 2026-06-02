"""
IPTV Scraper 配置
"""
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 数据库路径
DB_PATH = ROOT_DIR / "data" / "channels.db"

# M3U 输出
M3U_OUTPUT_PATH = ROOT_DIR / "data" / "playlist.m3u"
M3U_OUTPUT_FILENAME = "playlist.m3u"

# HTTP 服务
HOST = "0.0.0.0"
PORT = 5000

# 健康检查
HEALTH_CHECK_INTERVAL_MINUTES = 30      # 检查间隔
HEALTH_CHECK_TIMEOUT_SECONDS = 8        # 单源超时
MAX_FAIL_COUNT = 3                      # 连续失败标记为 inactive
MAX_CONCURRENT_CHECKS = 20              # 并发检查数
FFPROBE_TIMEOUT_SECONDS = 5             # ffprobe 探测超时

# 搜刮
SCRAPE_INTERVAL_HOURS = 6               # 全量搜刮间隔
AUTO_HEAL_INTERVAL_MINUTES = 15         # 自动修复检查间隔
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# GitHub IPTV 源仓库列表
GITHUB_M3U_SOURCES = [
    # ===== 大陆源 (CCTV + 卫视) =====
    {
        "name": "fanmingming/live (ipv6)",
        "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
        "region": "cn"
    },
    {
        "name": "YueChan/Live",
        "url": "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
        "region": "cn"
    },
    # ===== 全球源 (iptv-org, 按国家拆分) =====
    # iptv-org China 源已失效 (2026-06), 留空备用
    # {
    #     "name": "iptv-org China",
    #     "url": "https://iptv-org.github.io/iptv/countries/cn.m3u",
    #     "region": "cn"
    # },
    {
        "name": "iptv-org Hong Kong",
        "url": "https://iptv-org.github.io/iptv/countries/hk.m3u",
        "region": "hk"
    },
    {
        "name": "iptv-org Macau",
        "url": "https://iptv-org.github.io/iptv/countries/mo.m3u",
        "region": "macau"
    },
    {
        "name": "iptv-org Taiwan",
        "url": "https://iptv-org.github.io/iptv/countries/tw.m3u",
        "region": "tw"
    },
    # ===== 综合源 (Guovin/iptv-api) =====
    # 1792个频道 (IPv4+IPv6混合), 含完整的港澳台分组
    {
        "name": "Guovin/iptv-api (combined)",
        "url": "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u",
        "region": "all"
    },
    # ===== 大陆地方频道补充 (vbskycn) =====
    # 548个频道, 侧重地方台/数字台
    {
        "name": "vbskycn/iptv (ipv4)",
        "url": "https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.m3u",
        "region": "cn"
    },
    # ===== 每日聚合源 (zhi35) =====
    # 440个频道, 含16个港澳台源, 每日更新
    {
        "name": "zhi35 aggregated",
        "url": "https://live.zhi35.com/iptv.m3u",
        "region": "all"
    },
]

# Web 聚合站源列表
WEB_SCRAPE_SOURCES = [
    # 格式: (名称, URL, 解析规则类型)
    ("iptvcat", "https://iptvcat.com/", "table"),
    # 可扩展更多站点
]

# 频道组分类映射
GROUP_REGION_MAP = {
    # 大陆央视
    "央视": "mainland",
    "CCTV": "mainland",
    "中央": "mainland",
    # 大陆卫视
    "卫视": "mainland",
    "湖南": "mainland",
    "浙江": "mainland",
    "江苏": "mainland",
    "东方": "mainland",
    "广东": "mainland",
    "深圳": "mainland",
    "北京": "mainland",
    "上海": "mainland",
    # 香港
    "TVB": "hongkong",
    "翡翠": "hongkong",
    "明珠": "hongkong",
    "ViuTV": "hongkong",
    "viu": "hongkong",
    "HOY": "hongkong",
    "凤凰": "hongkong",
    "鳳凰": "hongkong",
    "无线": "hongkong",
    "無綫": "hongkong",
    "香港": "hongkong",
    "J2": "hongkong",
    "RTHK": "hongkong",
    "港台": "hongkong",
    # 澳门
    "澳视": "macau",
    "澳亚": "macau",
    "TDM": "macau",
    "澳门": "macau",
    # 台湾
    "台视": "taiwan",
    "中视": "taiwan",
    "华视": "taiwan",
    "民视": "taiwan",
    "公视": "taiwan",
    "八大": "taiwan",
    "三立": "taiwan",
    "TVBS": "taiwan",
    "东森": "taiwan",
    "東森": "taiwan",
    "緯來": "taiwan",
    "纬来": "taiwan",
    "靖天": "taiwan",
    "中天": "taiwan",
    "年代": "taiwan",
    "非凡": "taiwan",
    "壹電視": "taiwan",
    "寰宇": "taiwan",
}

# 用户自定义频道优先级（频道名 → 标签）
# 用于覆盖自动分组
CHANNEL_OVERRIDES = {
    # 示例: "凤凰卫视中文": "hongkong",
}
