"""
从在线直播源聚合站搜刮

支持的站点（需根据实际情况调整选择器）:
  - iptvcat.com
  - 直接爬取各电视官网（如 tv.cctv.com）
"""
import re
from typing import Optional, List
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from config import WEB_SCRAPE_SOURCES


class WebScraper(BaseScraper):
    """
    从多个在线直播源聚合站解析频道链接
    """

    def scrape(self) -> List[dict]:
        """爬取所有配置的 Web 源"""
        all_channels = []
        seen = set()

        for name, url, rule_type in WEB_SCRAPE_SOURCES:
            self.logger.info("  [Web] 爬取 %s (%s)...", name, url)
            channels = self._scrape_site(name, url, rule_type)
            for ch in channels:
                key = (ch["name"], ch["url"])
                if key not in seen:
                    seen.add(key)
                    all_channels.append(ch)
            self.logger.info("    → 找到 %d 个频道", len(channels))

        self.logger.info("  [Web] 共获得 %d 个频道（去重后）", len(all_channels))
        return all_channels

    def _scrape_site(self, site_name: str, url: str, rule_type: str) -> List[dict]:
        """爬取单个站点"""
        html = self._fetch(url)
        if not html:
            return []

        if rule_type == "table":
            return self._parse_table(html, site_name)
        elif rule_type == "list":
            return self._parse_list(html, site_name)
        else:
            return []

    def _parse_table(self, html: str, site_name: str) -> List[dict]:
        """解析表格型页面"""
        channels = []
        try:
            soup = BeautifulSoup(html, "lxml")
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        link = cells[1].find("a")
                        url = link.get("href") if link else cells[1].get_text(strip=True)

                        if name and url and url.startswith("http"):
                            channels.append({
                                "name": self._clean_name(name),
                                "url": url.strip(),
                                "group": "未分类",
                                "region": self._classify_region(name),
                                "logo": "",
                                "tvg_id": "",
                                "source": f"web:{site_name}",
                            })
        except Exception as e:
            self.logger.warning("解析失败 %s", e)

        return channels

    def _parse_list(self, html: str, site_name: str) -> List[dict]:
        """解析列表型页面"""
        channels = []
        try:
            soup = BeautifulSoup(html, "lxml")
            # 查找所有链接
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                text = a_tag.get_text(strip=True)
                if href.endswith(".m3u8") or ".m3u8" in href:
                    if text:
                        channels.append({
                            "name": self._clean_name(text),
                            "url": href.strip(),
                            "group": "未分类",
                            "region": self._classify_region(text),
                            "logo": "",
                            "tvg_id": "",
                            "source": f"web:{site_name}",
                        })
        except Exception as e:
            self.logger.warning("解析失败 %s", e)

        return channels

    def scrape_cctv(self) -> List[dict]:
        """
        专门爬取 CCTV 官网直播
        tv.cctv.com/live
        """
        channels = []
        url = "https://tv.cctv.com/live"
        html = self._fetch(url)
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "lxml")
            # CCTV 直播页面结构 - 查找频道列表
            for item in soup.select("a[href*='live']"):
                text = item.get_text(strip=True)
                href = item.get("href", "")
                if text and ("cctv" in href.lower() or text.startswith("CCTV")):
                    # 需要进一步获取播放页的 m3u8
                    ch = {
                        "name": self._clean_name(text),
                        "url": href,  # 页面URL，不是直接流
                        "group": "央视",
                        "region": "mainland",
                        "logo": "",
                        "tvg_id": "",
                        "source": "web:cctv",
                    }
                    channels.append(ch)
        except Exception as e:
            self.logger.warning("CCTV解析失败 %s", e)

        return channels
