"""
从 GitHub 公开 IPTV 仓库搜刮直播源

支持的源:
  - fanmingming/live (IPV6 央视/卫视/港澳台)
  - YanG-1989/m3u
  - iptv-org/iptv (按区域过滤)
"""
import re
from typing import Optional, List
from scrapers.base import BaseScraper
from config import GITHUB_M3U_SOURCES


class GitHubScraper(BaseScraper):
    """
    从 GitHub 上的 M3U 文件提取频道列表
    """

    def __init__(self):
        super().__init__()
        self.sources = GITHUB_M3U_SOURCES

    def scrape(self) -> List[dict]:
        """爬取所有配置的 GitHub M3U 源"""
        all_channels = []
        seen = set()  # (name, url) 去重

        for source in self.sources:
            self.logger.info("  [GitHub] 爬取 %s...", source['name'])
            channels = self._scrape_single_source(source)
            for ch in channels:
                key = (ch["name"], ch["url"])
                if key not in seen:
                    seen.add(key)
                    all_channels.append(ch)
            self.logger.info("    → 找到 %d 个频道", len(channels))

        self.logger.info("  [GitHub] 共获得 %d 个频道（去重后）", len(all_channels))
        return all_channels

    def _scrape_single_source(self, source: dict) -> List[dict]:
        """爬取单个 M3U 源"""
        m3u_content = self._fetch(source["url"])
        if not m3u_content:
            return []

        return self._parse_m3u(m3u_content, source)

    def _parse_m3u(self, content: str, source: dict) -> List[dict]:
        """解析 M3U 文件内容"""
        channels = []
        lines = content.strip().split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 收集前方的 KODIPROP 行 (DRM license 信息)
            kodi_props_lines = []
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("#KODIPROP:"):
                kodi_props_lines.insert(0, lines[j].strip())
                j -= 1
            kodi_props = "\n".join(kodi_props_lines)

            # 查找 EXTINF 行
            if line.startswith("#EXTINF:"):
                info_line = line
                url_line = ""

                # 获取下一行（URL）
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith("#"):
                        url_line = next_line
                        i += 1

                channel = self._parse_extinf(info_line, url_line, source, kodi_props)
                if channel:
                    channels.append(channel)
            i += 1

        return channels

    def _parse_extinf(self, info_line: str, url: str, source: dict, kodi_props: str = "") -> Optional[dict]:
        """解析单行 EXTINF"""
        if not url or url.startswith("#"):
            return None

        # 提取参数
        tvg_id = ""
        tvg_name = ""
        group_title = ""
        logo = ""

        # 提取 tvg-id
        m = re.search(r'tvg-id="([^"]*)"', info_line)
        if m:
            tvg_id = m.group(1)

        # 提取 tvg-name
        m = re.search(r'tvg-name="([^"]*)"', info_line)
        if m:
            tvg_name = m.group(1)

        # 提取 group-title
        m = re.search(r'group-title="([^"]*)"', info_line)
        if m:
            group_title = m.group(1)

        # 提取 tvg-logo
        m = re.search(r'tvg-logo="([^"]*)"', info_line)
        if m:
            logo = m.group(1)

        # 提取频道名（最后一个逗号后）
        channel_name = info_line.split(",")[-1].strip() if "," in info_line else ""
        channel_name = tvg_name or channel_name

        if not channel_name or not url:
            return None

        # 过滤非视频流 URL
        # 支持的协议: http/https/rtp/udp/rtsp
        is_valid_protocol = any(url.startswith(p) for p in ["http://", "https://", "rtp://", "udp://", "rtsp://"])
        is_valid_extension = any(url.endswith(ext) for ext in [".m3u8", ".ts", ".flv", ".mpd", ".smil"])
        has_stream_indicator = any(p in url for p in [".m3u8", ".ts", ".flv"])

        if not (is_valid_protocol and (is_valid_extension or has_stream_indicator)):
            # 宽松模式: 有 valid protocol 也保留（rtp/udp 可能不带扩展名）
            if not is_valid_protocol:
                return None

        # 区域判断
        target_raw = source.get("region", "all")
        detected_region = self._classify_region(channel_name, group_title)

        # 标准化区域代码 -> 内部名称
        REGION_MAP = {
            "cn": "mainland",
            "mainland": "mainland",
            "hk": "hongkong",
            "hongkong": "hongkong",
            "macau": "macau",
            "mo": "macau",
            "tw": "taiwan",
            "taiwan": "taiwan",
            "all": "all",
        }

        # 源指定区域优先（例如 iptv-org 按国家分类的 m3u）
        if target_raw != "all":
            final_region = REGION_MAP.get(target_raw, target_raw)
        else:
            final_region = detected_region

        channel_name = self._clean_name(channel_name)

        return {
            "name": channel_name,
            "url": url.strip(),
            "group": group_title or "未分类",
            "region": final_region,
            "logo": logo,
            "tvg_id": tvg_id,
            "source": f"github:{source['name']}",
            "kodi_props": kodi_props,
        }
