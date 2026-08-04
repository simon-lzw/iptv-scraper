"""
数据模型（全球版）
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class Channel:
    """电视频道（全球版）"""
    id: Optional[int] = None
    name: str = ""                     # 频道名, e.g. "CCTV-1 综合"
    url: str = ""                      # 直播源 URL
    group: str = ""                    # 分组, e.g. "大陆央视" / "News" / "Entertainment"
    region: str = "mainland"           # 旧区域: mainland/hongkong/macau/taiwan/international
    # ===== 全球扩展字段 =====
    country_code: str = ""             # ISO 3166-1 alpha-2, e.g. "CN"/"HK"/"JP"/"US"
    country_name_en: str = ""          # 英文名, e.g. "China"
    country_name_zh: str = ""          # 中文名, e.g. "中国"
    continent: str = ""                # 大区: asia/europe/north-america/...
    ip_version: str = ""               # ipv4/ipv6/domain/dual/unknown
    score: float = 0.0                 # 综合质量评分 0-100
    speed_kbps: float = 0.0            # 测速 KB/s
    original_name: str = ""            # 原始频道名
    # ===== 原有字段 =====
    kodi_props: str = ""               # KODIPROP DRM license metadata
    logo: str = ""                     # 台标 URL
    tvg_id: str = ""                   # EPG 节目表 ID
    source: str = ""                   # 来源 (哪个站抓的)
    is_active: bool = True             # 当前是否可用
    fail_count: int = 0                # 连续失败次数
    success_count: int = 0             # 连续成功次数
    response_time_ms: int = 0          # 最近响应时间(ms)
    last_checked: Optional[str] = None # 最后检查时间 ISO
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # 同频道多源（去重合并后）
    sources: List[dict] = field(default_factory=list)
    source_count: int = 0


@dataclass
class ScrapeRecord:
    """搜刮记录"""
    id: Optional[int] = None
    channel_name: str = ""
    source_website: str = ""
    url_found: str = ""
    success: bool = False
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class M3UEntry:
    """M3U 播放列表条目"""
    name: str
    url: str
    group: str = ""
    tvg_id: str = ""
    logo: str = ""
    region: str = "mainland"
    kodi_props: str = ""
    # 全球扩展
    country_code: str = ""
    country_name_zh: str = ""
