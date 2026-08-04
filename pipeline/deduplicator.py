"""
去重器

支持：
- URL 去重（规范化后完全相同只保留一次）
- 频道名 + URL 去重
- 同频道多源合并（保留所有源，按质量排序）
- URL 参数规范化（去除随机 token/时间戳参数）
"""
import re
from collections import defaultdict
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def normalize_url(url: str) -> str:
    """
    规范化 URL 用于去重比较：
    1. 去除 fragment
    2. 去除已知随机参数（token、sign、timestamp、_t、v、ts、expires 等）
    3. 参数排序
    4. 去除尾随斜杠差异
    """
    if not url:
        return ""
    url = url.strip()
    try:
        parsed = urlparse(url)
        # 去除 fragment
        parsed = parsed._replace(fragment="")
        # 过滤已知随机参数
        query = parse_qs(parsed.query, keep_blank_values=True)
        drop_keys = {"token", "sign", "timestamp", "ts", "_t", "t", "expires",
                     "expire", "auth_key", "key", "sig", "sig1", "time", "m3u8",
                     "hdnts", "hls", "playtoken", "v", "ver", "version"}
        filtered = {k: v for k, v in query.items() if k.lower() not in drop_keys}
        new_query = urlencode(sorted(filtered.items()), doseq=True)
        parsed = parsed._replace(query=new_query)
        # 规范化主机名小写
        if parsed.netloc:
            parsed = parsed._replace(netloc=parsed.netloc.lower())
        # 去除默认端口 80/443
        host = parsed.hostname or ""
        port = parsed.port
        netloc = host
        if port and port not in (80, 443):
            netloc = f"{host}:{port}"
        parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)
    except Exception:
        return url


def _channel_key(name: str) -> str:
    """频道名的规范化键（小写、去空格、去常见符号）"""
    if not name:
        return ""
    key = name.lower()
    key = re_sub_keep_cn(key)
    return key.strip()


def re_sub_keep_cn(text: str) -> str:
    """去除空格和常见符号但保留中文/字母/数字"""
    import re
    return re.sub(r"[\s\-_—()（）\[\]【】.:：,，。!！?？/\\|&·'\"`~]", "", text)


def deduplicate(channels: List[dict]) -> List[dict]:
    """
    去重主入口。
    输入: List[dict]，至少包含 name/url。
    输出: 去重后的频道列表；同频道多源合并为一个频道（sources 列表）。
    """
    # 1. URL 规范化去重
    seen_urls = set()
    unique = []
    for ch in channels:
        norm_url = normalize_url(ch.get("url", ""))
        if not norm_url:
            continue
        key = norm_url
        if key in seen_urls:
            continue
        seen_urls.add(key)
        ch["_norm_url"] = norm_url
        unique.append(ch)

    # 2. 按频道名聚合多源
    groups: dict = defaultdict(list)
    for ch in unique:
        key = _channel_key(ch.get("name", ""))
        if key:
            groups[key].append(ch)

    result = []
    for key, items in groups.items():
        # 按质量字段排序（score / response_time）
        items.sort(key=lambda c: (
            -float(c.get("score", 0) or 0),
            int(c.get("response_time_ms", 0) or 999999),
        ))
        primary = items[0]
        sources = [{"url": c.get("url"), "source": c.get("source", ""),
                    "score": c.get("score", 0), "response_time_ms": c.get("response_time_ms", 0)}
                   for c in items]
        primary["sources"] = sources
        primary["source_count"] = len(sources)
        result.append(primary)

    return result


def merge_sources(channels: List[dict]) -> List[dict]:
    """将同频道多源合并（若此前未合并），返回最终频道列表"""
    return deduplicate(channels)
