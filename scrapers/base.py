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
from config import USER_AGENT, GROUP_REGION_MAP


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
        # 注意: requests.Session 无 timeout 属性，超时统一在 _fetch(url, timeout=...) 显式传入


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
        """根据频道名/分组判断区域（与 main.py 共用 config.GROUP_REGION_MAP 单一数据源）"""
        text = name + group

        # ===== 排除误分类 =====
        # 杭州明珠是大陆地方台, 非TVB明珠台
        if "杭州明珠" in text or "六鳌翡翠湾" in text:
            return "mainland"

        # 统一查 GROUP_REGION_MAP（config 单一数据源，与 main.py._classify_region 一致）
        text_lower = text.lower()
        # 按关键词长度降序匹配：更长/更具体的关键词优先（避免"卫视"先命中"凤凰卫视"）
        for keyword, region in sorted(
            GROUP_REGION_MAP.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            if keyword.lower() in text_lower:
                return region

        return "mainland"  # default

    def _clean_name(self, name: str) -> str:
        """清理频道名"""
        name = name.strip()
        # 移除多余空格
        while "  " in name:
            name = name.replace("  ", " ")
        return name
