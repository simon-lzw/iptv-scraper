"""
多层级输出生成器

生成：
- output/all.m3u                    全球总频道
- output/Greater-China.m3u          中国大陆+港澳台
- output/countries/XX.m3u           各国家/地区独立文件
- output/metadata/countries.json    国家元数据
- output/metadata/channels.json     频道元数据

所有文件统一 UTF-8 无 BOM。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from models import Channel
from countries import get_country_name_zh, GREATER_CHINA_CODES, COUNTRIES, UNKNOWN_COUNTRY
from config import OUTPUT_DIR, OUTPUT_COUNTRIES_DIR, OUTPUT_METADATA_DIR


def _extinf(ch: Channel, group_title: str = "") -> str:
    """构建 EXTM3U 头部行"""
    attrs = []

    def esc(s: str) -> str:
        """转义引号和换行，防止破坏 M3U 格式"""
        return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")

    if ch.tvg_id:
        attrs.append(f'tvg-id="{esc(ch.tvg_id)}"')
    if ch.logo:
        attrs.append(f'tvg-logo="{esc(ch.logo)}"')
    # group-title 用中文名优先
    gt = group_title or ch.country_name_zh or ch.country_code
    attrs.append(f'group-title="{esc(gt)}"')
    attr_str = " ".join(attrs)
    return f'#EXTINF:-1 {attr_str},{esc(ch.name)}'


def _write_m3u(path: Path, channels: List[Channel], title: str,
               group_by_country: bool = True) -> int:
    """写入 M3U 文件，返回频道数"""
    path.parent.mkdir(parents=True, exist_ok=True)
    # 未知国家（ZZ）不输出到按国家分组的文件
    visible = [c for c in channels if c.country_code != UNKNOWN_COUNTRY]
    lines = [
        "#EXTM3U",
        f"#PLAYLIST: {title}",
        f"#生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"#频道数: {len(visible)}",
        "",
    ]
    # 按国家分组输出
    by_country: Dict[str, List[Channel]] = {}
    for ch in visible:
        by_country.setdefault(ch.country_code, []).append(ch)

    for code in sorted(by_country.keys()):
        country_zh = get_country_name_zh(code)
        lines.append(f'# ===== {country_zh} ({code}) =====')
        lines.append("")
        for ch in by_country[code]:
            lines.append(_extinf(ch))
            lines.append(ch.url)
            lines.append("")
        lines.append("")

    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8", newline="\n")
    return len(visible)


def generate_all(channels: List[Channel]) -> Path:
    """生成全球总文件"""
    path = OUTPUT_DIR / "all.m3u"
    _write_m3u(path, channels, "全球 IPTV 直播源")
    return path


def generate_greater_china(channels: List[Channel]) -> Path:
    """生成中国大陆+港澳台汇总文件"""
    gc = [c for c in channels if c.country_code in GREATER_CHINA_CODES]
    path = OUTPUT_DIR / "Greater-China.m3u"
    _write_m3u(path, gc, "中国大陆/香港/澳门/台湾 IPTV 直播源")
    return path


def generate_by_country(channels: List[Channel]) -> Dict[str, Path]:
    """生成各国家/地区独立文件"""
    paths = {}
    by_country: Dict[str, List[Channel]] = {}
    for ch in channels:
        if ch.country_code and ch.country_code != UNKNOWN_COUNTRY:
            by_country.setdefault(ch.country_code, []).append(ch)

    for code, chs in by_country.items():
        country_zh = get_country_name_zh(code)
        path = OUTPUT_COUNTRIES_DIR / f"{code}.m3u"
        _write_m3u(path, chs, f"{country_zh} ({code}) IPTV 直播源", group_by_country=False)
        paths[code] = path
    return paths


def generate_metadata(channels: List[Channel]) -> Dict[str, Path]:
    """生成 JSON 元数据"""
    OUTPUT_METADATA_DIR.mkdir(parents=True, exist_ok=True)

    # countries.json
    country_stats: Dict[str, dict] = {}
    for ch in channels:
        code = ch.country_code or UNKNOWN_COUNTRY
        info = COUNTRIES.get(code, {})
        stat = country_stats.setdefault(code, {
            "code": code,
            "name_en": info.get("en", code),
            "name_zh": info.get("zh", code),
            "region": info.get("region", ""),
            "channel_count": 0,
        })
        stat["channel_count"] += 1
    countries_path = OUTPUT_METADATA_DIR / "countries.json"
    countries_path.write_text(
        json.dumps(list(country_stats.values()), ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )

    # channels.json
    channel_list = []
    for ch in channels:
        channel_list.append({
            "name": ch.name,
            "url": ch.url,
            "group": ch.group,
            "country_code": ch.country_code,
            "country_name_zh": ch.country_name_zh,
            "ip_version": ch.ip_version,
            "score": ch.score,
            "source": ch.source,
            "is_active": ch.is_active,
        })
    channels_path = OUTPUT_METADATA_DIR / "channels.json"
    channels_path.write_text(
        json.dumps(channel_list, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    return {"countries": countries_path, "channels": channels_path}


def generate_all_outputs(channels: List[Channel]) -> dict:
    """生成全部输出文件"""
    all_path = generate_all(channels)
    gc_path = generate_greater_china(channels)
    country_paths = generate_by_country(channels)
    meta_paths = generate_metadata(channels)
    return {
        "all": all_path,
        "greater_china": gc_path,
        "countries": country_paths,
        "metadata": meta_paths,
        "channel_count": len(channels),
        "country_count": len(country_paths),
    }
