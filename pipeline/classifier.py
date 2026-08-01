"""
国家/地区自动分类器

综合利用：
1. 原始 IPTV 分类 (group-title)
2. 频道名称
3. URL 域名 / TLD
4. 数据源自身提供的国家/地区信息
5. 维护的国家/地区映射表

无法可靠判断 → Unknown (ZZ)，不强行归类。
"""
import re
from urllib.parse import urlparse
from typing import Optional
from countries import COUNTRY_KEYWORDS, TLD_COUNTRY_MAP, UNKNOWN_COUNTRY, COUNTRIES

# group-title 中的国家/地区名 → 代码（英文/中文）
GROUP_COUNTRY_MAP = {}
for code, info in COUNTRIES.items():
    GROUP_COUNTRY_MAP[info["en"].lower()] = code
    GROUP_COUNTRY_MAP[info["zh"]] = code
# 常见别名
GROUP_COUNTRY_MAP.update({
    "china mainland": "CN", "mainland china": "CN", "mainland": "CN", "中国": "CN",
    "hongkong": "HK", "hong kong": "HK", "hk": "HK", "香港": "HK",
    "macau": "MO", "macao": "MO", "mo": "MO", "澳门": "MO",
    "taiwan": "TW", "tw": "TW", "台湾": "TW",
    "south korea": "KR", "korea": "KR", "韩国": "KR",
    "united states": "US", "usa": "US", "us": "US", "美国": "US",
    "united kingdom": "GB", "uk": "GB", "gb": "GB", "英国": "GB",
    "uae": "AE", "united arab emirates": "AE", "阿联酋": "AE",
    "saudi arabia": "SA", "沙特": "SA",
    "russia": "RU", "俄罗斯": "RU",
    "czechia": "CZ", "czech republic": "CZ", "捷克": "CZ",
    "australia": "AU", "澳大利亚": "AU",
    "new zealand": "NZ", "新西兰": "NZ",
    "south africa": "ZA", "南非": "ZA",
    "philippines": "PH", "菲律宾": "PH",
    "vietnam": "VN", "越南": "VN",
    "thailand": "TH", "泰国": "TH",
    "singapore": "SG", "新加坡": "SG",
    "malaysia": "MY", "马来西亚": "MY",
    "indonesia": "ID", "印尼": "ID",
    "india": "IN", "印度": "IN",
    "türkiye": "TR", "turkey": "TR", "土耳其": "TR",
    "israel": "IL", "以色列": "IL",
    "brazil": "BR", "巴西": "BR",
    "mexico": "MX", "墨西哥": "MX",
    "canada": "CA", "加拿大": "CA",
    "germany": "DE", "德国": "DE",
    "france": "FR", "法国": "FR",
    "italy": "IT", "意大利": "IT",
    "spain": "ES", "西班牙": "ES",
    "netherlands": "NL", "荷兰": "NL",
    "poland": "PL", "波兰": "PL",
    "portugal": "PT", "葡萄牙": "PT",
    "sweden": "SE", "瑞典": "SE",
    "switzerland": "CH", "瑞士": "CH",
    "austria": "AT", "奥地利": "AT",
    "belgium": "BE", "比利时": "BE",
    "norway": "NO", "挪威": "NO",
    "denmark": "DK", "丹麦": "DK",
    "finland": "FI", "芬兰": "FI",
    "greece": "GR", "希腊": "GR",
    "ireland": "IE", "爱尔兰": "IE",
    "ukraine": "UA", "乌克兰": "UA",
    "argentina": "AR", "阿根廷": "AR",
    "chile": "CL", "智利": "CL",
    "colombia": "CO", "哥伦比亚": "CO",
    "peru": "PE", "秘鲁": "PE",
    "egypt": "EG", "埃及": "EG",
    "nigeria": "NG", "尼日利亚": "NG",
    "morocco": "MA", "摩洛哥": "MA",
    "kenya": "KE", "肯尼亚": "KE",
    "ghana": "GH", "加纳": "GH",
    "ethiopia": "ET", "埃塞俄比亚": "ET",
    "tanzania": "TZ", "坦桑尼亚": "TZ",
    "japan": "JP", "日本": "JP",
})


def _classify_by_group(group: str) -> Optional[str]:
    """从 group-title 判断国家"""
    if not group:
        return None
    g = group.strip().lower()
    # 尝试完整匹配
    if g in GROUP_COUNTRY_MAP:
        return GROUP_COUNTRY_MAP[g]
    # 尝试包含匹配（如 "Japan" in "Japan TV"）
    for kw, code in GROUP_COUNTRY_MAP.items():
        if len(kw) >= 3 and kw in g:
            return code
    return None


def _classify_by_name(name: str) -> Optional[str]:
    """从频道名判断国家"""
    if not name:
        return None
    text = name.lower()
    # 先尝试精确关键词（CN 单独处理避免误判）
    # 按关键词长度降序，优先匹配长关键词；字母关键词用单词边界匹配
    candidates = []
    for code, kws in COUNTRY_KEYWORDS.items():
        for kw in kws:
            k = kw.lower()
            if k in text:
                # 字母/数字关键词需要单词边界，避免 "international" 误匹配 "inter"
                if k[0].isalnum() and k[-1].isalnum():
                    if re.search(r"(^|[^a-z0-9])" + re.escape(k) + r"([^a-z0-9]|$)", text):
                        candidates.append((len(k), code))
                else:
                    candidates.append((len(k), code))
    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]
    return None


def _classify_by_url(url: str) -> Optional[str]:
    """从 URL 域名/TLD 判断国家"""
    if not url:
        return None
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return None
    host = host.lower()
    # 知名域名直接映射
    known = {
        "tvb.com": "HK", "rthk.hk": "HK", "viutv.com": "HK",
        "nhk.or.jp": "JP", "fujitv.co.jp": "JP",
        "kbs.co.kr": "KR", "imbc.com": "KR", "sbs.co.kr": "KR",
        "bbc.co.uk": "GB", "itv.com": "GB",
        "cnn.com": "US", "abc.go.com": "US", "nbc.com": "US", "cbs.com": "US",
        "fox.com": "US", "hbo.com": "US", "espn.com": "US",
        "tf1.fr": "FR", "france.tv": "FR",
        "zdf.de": "DE", "ard.de": "DE",
        "rai.it": "IT",
        "rtve.es": "ES",
        "abc.net.au": "AU", "nine.com.au": "AU",
        "cbc.ca": "CA",
        "globo.com": "BR",
        "televisa.com": "MX",
        "sabc.co.za": "ZA",
        "mediacorp.sg": "SG",
        "astro.com.my": "MY",
        "vtv.vn": "VN",
        "thairath.co.th": "TH",
        "abs-cbn.com": "PH",
        "tvri.go.id": "ID",
        "ddindia.gov.in": "IN",
        "trt.net.tr": "TR",
        "aljazeera.com": "QA",
    }
    for domain, code in known.items():
        if host == domain or host.endswith("." + domain):
            return code
    # TLD 判断
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in TLD_COUNTRY_MAP:
        return TLD_COUNTRY_MAP[tld]
    return None


def classify_country(name: str = "", group: str = "", url: str = "",
                     source_region: str = "") -> str:
    """
    综合判断国家/地区代码。
    优先级：source_region 显式指定 > group-title > 频道名 > URL 域名/TLD
    """
    # 1. 数据源显式指定（如 iptv-org 的 region 参数 / 旧 region 值）
    if source_region:
        r = source_region.strip().upper()
        # 旧 region 值映射（mainland/hongkong/macau/taiwan/international）
        old_map = {"MAINLAND": "CN", "HONGKONG": "HK", "MACAU": "MO", "TAIWAN": "TW"}
        if r in old_map:
            return old_map[r]
        # 直接国家代码或别名
        if r in COUNTRIES:
            return r
        # 单字母/区域兜底：尝试 GROUP_COUNTRY_MAP
        alias = GROUP_COUNTRY_MAP.get(source_region.strip().lower())
        if alias:
            return alias

    # 2. group-title
    code = _classify_by_group(group)
    if code:
        return code

    # 3. 频道名
    code = _classify_by_name(name)
    if code:
        return code

    # 4. URL 域名/TLD
    code = _classify_by_url(url)
    if code:
        return code

    return UNKNOWN_COUNTRY


def region_to_country(region: str) -> str:
    """旧 region 值 → 国家代码"""
    mapping = {
        "mainland": "CN",
        "hongkong": "HK",
        "macau": "MO",
        "taiwan": "TW",
        "international": "ZZ",
    }
    return mapping.get(region, region.upper() if region.isalpha() and len(region) == 2 else "ZZ")
