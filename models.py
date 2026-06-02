"""
数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Channel:
    """电视频道"""
    id: Optional[int] = None
    name: str = ""                     # 频道名, e.g. "CCTV-1 综合"
    url: str = ""                      # 直播源 URL
    group: str = ""                    # 分组, e.g. "大陆央视"
    region: str = "mainland"
    kodi_props: str = ""           # 区域: mainland / hongkong / macau / taiwan / international
    logo: str = ""                     # 台标 URL
    tvg_id: str = ""                   # EPG 节目表 ID
    source: str = ""                   # 来源 (哪个站抓的)
    is_active: bool = True             # 当前是否可用
    fail_count: int = 0                # 连续失败次数
    success_count: int = 0             # 连续成功次数
    response_time_ms: int = 0          # 最近响应时间(ms)
    last_checked: Optional[str] = None # 最后检查时间 ISO
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    kodi_props: str = ""               # KODIPROP DRM license metadata
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


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
