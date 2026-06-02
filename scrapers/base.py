"""
爬虫基类
"""
import time
import random
from abc import ABC, abstractmethod
from typing import Optional, List
import requests
import urllib.request
import ssl
import logging
from config import USER_AGENT


class BaseScraper(ABC):
    """搜刮器基类"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.session.timeout = 15


    @abstractmethod
    def scrape(self) -> List[dict]:
        """
        搜刮直播源
        返回: [{"name": "...", "url": "...", "group": "...", "region": "...", "logo": "..."}]
        """
        ...

    def _fetch(self, url: str, timeout: int = 15, max_retries: int = 3) -> Optional[str]:
        """安全 HTTP GET，带指数退避重试 + urllib SSL降级"""
        for attempt in range(max_retries):
            try:
                resp = self.session.get(url, timeout=timeout)
                resp.raise_for_status()
                return resp.text
            except (ValueError, requests.exceptions.SSLError):
                # SSL/ValueError (如 Windows Python 3.8 代理问题) → 降级到 urllib
                self.logger.warning("SSL/ValueError, 降级到 urllib: %s", url[:60])
                try:
                    import gzip
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    req = urllib.request.Request(url, headers=dict(self.session.headers))
                    req.add_header("Accept-Encoding", "gzip, deflate")
                    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                        raw = resp.read()
                        # 自动解压 gzip
                        if resp.headers.get("Content-Encoding") == "gzip":
                            raw = gzip.decompress(raw)
                        return raw.decode("utf-8", errors="replace")
                except Exception as e2:
                    self.logger.warning("urllib 也失败: %s", str(e2)[:40])
                    return None
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429 and attempt < max_retries - 1:
                    # 429 Too Many Requests = 需要退避
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning("请求被限流 (429)，等待 %.1fs 后重试 (%d/%d)...",
                                        wait, attempt + 1, max_retries)
                    time.sleep(wait)
                    continue
                self.logger.warning("请求失败 %s: HTTP %s", url[:60], status)
                return None
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning("连接异常 (%s)，等待 %.1fs 后重试 (%d/%d)...",
                                        str(e)[:30], wait, attempt + 1, max_retries)
                    time.sleep(wait)
                    continue
                self.logger.warning("请求失败 %s: %s", url[:60], e)
                return None
            except Exception as e:
                self.logger.warning("请求失败 %s: %s", url[:60], e)
                return None
        return None

    def _classify_region(self, name: str, group: str = "") -> str:
        """根据频道名/分组判断区域"""
        text = name + group

        # ===== 排除误分类 =====
        # 杭州明珠是大陆地方台, 非TVB明珠台
        if "杭州明珠" in text or "六鳌翡翠湾" in text:
            return "mainland"

        # 香港特征
        hk_keywords = [
            "tvb", "翡翠", "明珠", "viutv", "viu", "hoy",
            "凤凰", "鳳凰", "香港", "有線", "无线", "無綫",
            "星河", "剧集", "jade", "pearl", "j2",
            "rthk", "港台", "無線",
        ]
        for kw in hk_keywords:
            if kw in text:
                return "hongkong"

        # 澳门特征
        macau_keywords = ["澳视", "澳視", "澳亚", "澳亞", "tdm", "澳门", "macau"]
        for kw in macau_keywords:
            if kw in text:
                return "macau"

        # 台湾特征
        tw_keywords = [
            "台視", "台视", "中視", "中视", "華視", "华视", "民視", "民视",
            "公視", "公视", "八大", "三立", "tvbs", "東森", "东森",
            "緯來", "纬来", "中天", "年代", "非凡", "壹電視", "壹电视",
            "寰宇", "卫视中文", "靖天",
        ]
        for kw in tw_keywords:
            if kw in text:
                return "taiwan"

        # 大陆特征
        cn_keywords = ["cctv", "央视", "卫视", "湖南", "浙江", "江苏",
                       "东方卫视", "广东", "深圳", "北京", "cgtn"]
        for kw in cn_keywords:
            if kw in text:
                return "mainland"

        return "mainland"  # default

    def _clean_name(self, name: str) -> str:
        """清理频道名"""
        name = name.strip()
        # 移除多余空格
        while "  " in name:
            name = name.replace("  ", " ")
        return name
