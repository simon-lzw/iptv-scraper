"""
M3U 播放列表生成器

输出标准 M3U 格式，兼容 TiviMate / VLC / Kodi / IPTV Smarters 等
"""
from datetime import datetime
from pathlib import Path
from models import Channel, M3UEntry
from config import M3U_OUTPUT_PATH, GROUP_REGION_MAP
from typing import List, Dict, Union



class M3UGenerator:
    """生成 IPTV 标准的 M3U 播放列表"""

    # 区域显示名称
    REGION_LABELS = {
        "mainland": "📺 中国大陆",
        "hongkong": "🇭🇰 香港",
        "macau": "🇲🇴 澳门",
        "taiwan": "🇹🇼 台湾",
        "international": "🌐 国际",
    }

    # 分组排序优先级
    GROUP_ORDER = {
        "mainland": [
            "央视", "CCTV", "中央",
            "卫视",
            "广东",
            "其他",
        ],
        "hongkong": [],
        "macau": [],
        "taiwan": [],
    }

    def __init__(self, output_path: Union[str, Path] = M3U_OUTPUT_PATH):
        self.output_path = Path(output_path)

    def generate(self, channels: List[Channel]) -> str:
        """
        从频道列表生成 M3U 内容
        按区域 → 分组 → 名称排序
        """
        entries = self._channels_to_entries(channels)
        m3u = self._build_m3u(entries)
        self._write(m3u)
        return m3u

    def _channels_to_entries(self, channels: List[Channel]) -> List[M3UEntry]:
        """Channel 列表转为 M3UEntry 列表"""
        entries = []
        for ch in channels:
            entries.append(M3UEntry(
                name=ch.name,
                url=ch.url,
                group=self._normalize_group(ch.group, ch.name),
                tvg_id=ch.tvg_id,
                logo=ch.logo,
                region=ch.region,
                kodi_props=ch.kodi_props,
            ))
        return entries

    def _normalize_group(self, group: str, name: str) -> str:
        """标准化分组名"""
        if group and group != "未分类":
            return group

        # 从频道名推断分组
        name_upper = name.upper()
        if name_upper.startswith("CCTV"):
            return "央视"
        if "卫视" in name:
            return "卫视"
        if any(k in name for k in ["TVB", "ViuTV", "HOY"]):
            return "香港频道"
        if any(k in name for k in ["台视", "中视", "华视", "民视", "公视"]):
            return "台湾无线台"
        if "CGTN" in name_upper:
            return "央视"

        return group or "其他"

    def _build_m3u(self, entries: List[M3UEntry]) -> str:
        """构建 M3U 文件内容"""
        lines = [
            '#EXTM3U',
            f'#PLAYLIST: IPTV 直播源 (生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")})',
            f'#总频道数: {len(entries)}',
            '',
        ]

        # 按区域分组
        region_groups: Dict[str, List[M3UEntry]] = {}
        for e in entries:
            region_groups.setdefault(e.region, []).append(e)

        # 按区域顺序输出
        region_order = ["mainland", "hongkong", "macau", "taiwan", "international"]

        for region in region_order:
            if region not in region_groups:
                continue
            region_entries = region_groups[region]

            # 区域内按 group 分组
            group_dict: Dict[str, List[M3UEntry]] = {}
            for e in region_entries:
                group_dict.setdefault(e.group, []).append(e)

            # 区域标题
            label = self.REGION_LABELS.get(region, region)
            lines.append(f'# ===== {label} =====')
            lines.append('')

            # 组排序
            group_order = self.GROUP_ORDER.get(region, [])
            sorted_groups = sorted(
                group_dict.items(),
                key=lambda x: (group_order.index(x[0]) if x[0] in group_order else 999, x[0])
            )

            for group_name, group_entries in sorted_groups:
                lines.append(f'# --- {group_name} ---')
                # 组内按名称排序
                for e in sorted(group_entries, key=lambda x: x.name):
                    # 如果频道有 KODIPROP DRM 信息，在 EXTINF 前输出
                    if e.kodi_props:
                        for prop_line in e.kodi_props.split("\n"):
                            lines.append(prop_line)
                    extinf_parts = [
                        '#EXTINF:-1',
                    ]
                    if e.tvg_id:
                        extinf_parts.append(f'tvg-id="{e.tvg_id}"')
                    if e.name:
                        extinf_parts.append(f'tvg-name="{e.name}"')
                    if e.logo:
                        extinf_parts.append(f'tvg-logo="{e.logo}"')
                    if e.group:
                        extinf_parts.append(f'group-title="{e.group}"')

                    extinf_parts.append(f',{e.name}')
                    lines.append(' '.join(extinf_parts))
                    lines.append(e.url)
                    lines.append('')
                lines.append('')

        return '\n'.join(lines)

    def _write(self, content: str):
        """写入文件"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(content, encoding="utf-8")
        print(f"  [M3U] 已写入 {self.output_path} ({len(content)} 字节)")

    def get_output_path(self) -> Path:
        return self.output_path
