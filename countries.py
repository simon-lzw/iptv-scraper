"""
国家/地区映射表 (ISO 3166-1 alpha-2)

统一维护国家代码、英文名、中文名和所属大区。
用于频道分类、输出文件命名、JSON 元数据。
"""
from typing import Dict, Optional

# 国家/地区: code -> {en, zh, region}
# region: asia / europe / north-america / south-america / oceania / africa / middle-east
COUNTRIES: Dict[str, dict] = {
    # ===== 亚洲 =====
    "CN": {"en": "China", "zh": "中国", "region": "asia"},
    "HK": {"en": "Hong Kong", "zh": "香港", "region": "asia"},
    "MO": {"en": "Macau", "zh": "澳门", "region": "asia"},
    "TW": {"en": "Taiwan", "zh": "台湾", "region": "asia"},
    "JP": {"en": "Japan", "zh": "日本", "region": "asia"},
    "KR": {"en": "South Korea", "zh": "韩国", "region": "asia"},
    "KP": {"en": "North Korea", "zh": "朝鲜", "region": "asia"},
    "SG": {"en": "Singapore", "zh": "新加坡", "region": "asia"},
    "MY": {"en": "Malaysia", "zh": "马来西亚", "region": "asia"},
    "TH": {"en": "Thailand", "zh": "泰国", "region": "asia"},
    "VN": {"en": "Vietnam", "zh": "越南", "region": "asia"},
    "PH": {"en": "Philippines", "zh": "菲律宾", "region": "asia"},
    "ID": {"en": "Indonesia", "zh": "印度尼西亚", "region": "asia"},
    "IN": {"en": "India", "zh": "印度", "region": "asia"},
    "PK": {"en": "Pakistan", "zh": "巴基斯坦", "region": "asia"},
    "BD": {"en": "Bangladesh", "zh": "孟加拉国", "region": "asia"},
    "LK": {"en": "Sri Lanka", "zh": "斯里兰卡", "region": "asia"},
    "NP": {"en": "Nepal", "zh": "尼泊尔", "region": "asia"},
    "MM": {"en": "Myanmar", "zh": "缅甸", "region": "asia"},
    "KH": {"en": "Cambodia", "zh": "柬埔寨", "region": "asia"},
    "LA": {"en": "Laos", "zh": "老挝", "region": "asia"},
    "BN": {"en": "Brunei", "zh": "文莱", "region": "asia"},
    "MN": {"en": "Mongolia", "zh": "蒙古", "region": "asia"},
    "KZ": {"en": "Kazakhstan", "zh": "哈萨克斯坦", "region": "asia"},
    "UZ": {"en": "Uzbekistan", "zh": "乌兹别克斯坦", "region": "asia"},
    # ===== 中东 =====
    "AE": {"en": "United Arab Emirates", "zh": "阿联酋", "region": "middle-east"},
    "SA": {"en": "Saudi Arabia", "zh": "沙特阿拉伯", "region": "middle-east"},
    "IL": {"en": "Israel", "zh": "以色列", "region": "middle-east"},
    "TR": {"en": "Turkey", "zh": "土耳其", "region": "middle-east"},
    "IR": {"en": "Iran", "zh": "伊朗", "region": "middle-east"},
    "QA": {"en": "Qatar", "zh": "卡塔尔", "region": "middle-east"},
    "KW": {"en": "Kuwait", "zh": "科威特", "region": "middle-east"},
    "OM": {"en": "Oman", "zh": "阿曼", "region": "middle-east"},
    "BH": {"en": "Bahrain", "zh": "巴林", "region": "middle-east"},
    "LB": {"en": "Lebanon", "zh": "黎巴嫩", "region": "middle-east"},
    "JO": {"en": "Jordan", "zh": "约旦", "region": "middle-east"},
    # ===== 欧洲 =====
    "GB": {"en": "United Kingdom", "zh": "英国", "region": "europe"},
    "FR": {"en": "France", "zh": "法国", "region": "europe"},
    "DE": {"en": "Germany", "zh": "德国", "region": "europe"},
    "IT": {"en": "Italy", "zh": "意大利", "region": "europe"},
    "ES": {"en": "Spain", "zh": "西班牙", "region": "europe"},
    "PT": {"en": "Portugal", "zh": "葡萄牙", "region": "europe"},
    "NL": {"en": "Netherlands", "zh": "荷兰", "region": "europe"},
    "BE": {"en": "Belgium", "zh": "比利时", "region": "europe"},
    "CH": {"en": "Switzerland", "zh": "瑞士", "region": "europe"},
    "AT": {"en": "Austria", "zh": "奥地利", "region": "europe"},
    "SE": {"en": "Sweden", "zh": "瑞典", "region": "europe"},
    "NO": {"en": "Norway", "zh": "挪威", "region": "europe"},
    "DK": {"en": "Denmark", "zh": "丹麦", "region": "europe"},
    "FI": {"en": "Finland", "zh": "芬兰", "region": "europe"},
    "PL": {"en": "Poland", "zh": "波兰", "region": "europe"},
    "CZ": {"en": "Czechia", "zh": "捷克", "region": "europe"},
    "SK": {"en": "Slovakia", "zh": "斯洛伐克", "region": "europe"},
    "HU": {"en": "Hungary", "zh": "匈牙利", "region": "europe"},
    "RO": {"en": "Romania", "zh": "罗马尼亚", "region": "europe"},
    "BG": {"en": "Bulgaria", "zh": "保加利亚", "region": "europe"},
    "GR": {"en": "Greece", "zh": "希腊", "region": "europe"},
    "RU": {"en": "Russia", "zh": "俄罗斯", "region": "europe"},
    "UA": {"en": "Ukraine", "zh": "乌克兰", "region": "europe"},
    "IE": {"en": "Ireland", "zh": "爱尔兰", "region": "europe"},
    "IS": {"en": "Iceland", "zh": "冰岛", "region": "europe"},
    "EE": {"en": "Estonia", "zh": "爱沙尼亚", "region": "europe"},
    "LV": {"en": "Latvia", "zh": "拉脱维亚", "region": "europe"},
    "LT": {"en": "Lithuania", "zh": "立陶宛", "region": "europe"},
    "HR": {"en": "Croatia", "zh": "克罗地亚", "region": "europe"},
    "RS": {"en": "Serbia", "zh": "塞尔维亚", "region": "europe"},
    "SI": {"en": "Slovenia", "zh": "斯洛文尼亚", "region": "europe"},
    # ===== 北美洲 =====
    "US": {"en": "United States", "zh": "美国", "region": "north-america"},
    "CA": {"en": "Canada", "zh": "加拿大", "region": "north-america"},
    "MX": {"en": "Mexico", "zh": "墨西哥", "region": "north-america"},
    # ===== 南美洲 =====
    "BR": {"en": "Brazil", "zh": "巴西", "region": "south-america"},
    "AR": {"en": "Argentina", "zh": "阿根廷", "region": "south-america"},
    "CL": {"en": "Chile", "zh": "智利", "region": "south-america"},
    "CO": {"en": "Colombia", "zh": "哥伦比亚", "region": "south-america"},
    "PE": {"en": "Peru", "zh": "秘鲁", "region": "south-america"},
    "VE": {"en": "Venezuela", "zh": "委内瑞拉", "region": "south-america"},
    "UY": {"en": "Uruguay", "zh": "乌拉圭", "region": "south-america"},
    "PY": {"en": "Paraguay", "zh": "巴拉圭", "region": "south-america"},
    "EC": {"en": "Ecuador", "zh": "厄瓜多尔", "region": "south-america"},
    "BO": {"en": "Bolivia", "zh": "玻利维亚", "region": "south-america"},
    # ===== 大洋洲 =====
    "AU": {"en": "Australia", "zh": "澳大利亚", "region": "oceania"},
    "NZ": {"en": "New Zealand", "zh": "新西兰", "region": "oceania"},
    # ===== 非洲 =====
    "ZA": {"en": "South Africa", "zh": "南非", "region": "africa"},
    "EG": {"en": "Egypt", "zh": "埃及", "region": "africa"},
    "NG": {"en": "Nigeria", "zh": "尼日利亚", "region": "africa"},
    "MA": {"en": "Morocco", "zh": "摩洛哥", "region": "africa"},
    "KE": {"en": "Kenya", "zh": "肯尼亚", "region": "africa"},
    "GH": {"en": "Ghana", "zh": "加纳", "region": "africa"},
    "ET": {"en": "Ethiopia", "zh": "埃塞俄比亚", "region": "africa"},
    "TZ": {"en": "Tanzania", "zh": "坦桑尼亚", "region": "africa"},
}

# 中国大陆 + 香港 + 澳门 + 台湾 汇总地区代码
GREATER_CHINA_CODES = ["CN", "HK", "MO", "TW"]

# 频道名/关键词 → 国家代码（用于分类）
# 优先匹配更具体的词
COUNTRY_KEYWORDS: Dict[str, list] = {
    "CN": ["央视", "cctv", "cgtn", "湖南", "浙江", "江苏", "东方卫视", "广东", "深圳", "北京卫视",
           "上海", "天津", "重庆", "山东", "河南", "四川", "福建", "湖北", "陕西", "云南", "贵州",
           "广西", "江西", "安徽", "河北", "山西", "辽宁", "吉林", "黑龙江", "新疆", "西藏", "内蒙古",
           "宁夏", "青海", "甘肃", "海南", "china", "beijing", "shanghai", "guangdong", "凤凰卫视中文"],
    "HK": ["tvb", "翡翠", "明珠", "viutv", "viu", "hoy", "凤凰", "鳳凰", "香港", "有線", "无线", "無綫",
           "星河", "jade", "pearl", "j2", "rthk", "港台", "hong kong", "tvb news"],
    "MO": ["澳视", "澳視", "澳亚", "澳亞", "tdm", "澳门", "macau", "macao"],
    "TW": ["台視", "台视", "中視", "中视", "華視", "华视", "民視", "民视", "公視", "公视",
           "八大", "三立", "tvbs", "東森", "东森", "緯來", "纬来", "中天", "年代", "非凡",
           "壹電視", "壹电视", "寰宇", "卫视中文", "靖天", "taiwan", "台视新闻"],
    "JP": ["nhk", "日本", "東京", "东京", "fujitv", "fuji", "ntv", "朝日", "tv tokyo", "tokyo mx",
           "tbs", "japan", "japanese", "bs", "wowow"],
    "KR": ["kbs", "mbc", "sbs", "韩国", "首尔", "korea", "korean", "jtbc", "tvn", "tvN", "arirang"],
    "KP": ["朝鲜", "north korea", "korean central"],
    "US": ["cnn", "abc", "nbc", "cbs", "fox", "hbo", "espn", "discovery", "national geographic",
           "nat geo", "history channel", "cartoon network", "nickelodeon", "disney", "paramount",
           "tnt", "usa", "united states", "american", "hollywood", "nba tv", "nfl", "mtv", "cnbc", "msnbc"],
    "GB": ["bbc", "itv", "sky", "channel 4", "channel 5", "britain", "united kingdom", "uk tv", "eurosport uk"],
    "FR": ["france", "french", "tf1", "france2", "france 2", "france3", "canal+", "canal plus", "arte", "bfmtv", "m6"],
    "DE": ["germany", "german", "ard", "zdf", "das erste", "rtl", "prosieben", "sat.1", "vox", "ntv"],
    "IT": ["italy", "italian", "rai", "rai1", "rai 1", "mediaset", "canale 5", "italia 1", "sky italia", "la7"],
    "ES": ["spain", "spanish", "tve", "la 1", "la1", "antena 3", "cuatro", "telecinco", "la sexta", "movistar"],
    "PT": ["portugal", "portuguese", "rtp", "rtp1", "sic", "tvi", "sport tv"],
    "NL": ["netherlands", "dutch", "npo", "npo1", "npo 1", "rtl4", "sbs6", "veronica"],
    "BE": ["belgium", "belgian", "rtbf", "vrt", "la une", "een", "canvas"],
    "SE": ["sweden", "swedish", "svt", "svt1", "tv4", "tv3", "kanal5"],
    "NO": ["norway", "norwegian", "nrk", "nrk1", "tv2", "tv norge"],
    "DK": ["denmark", "danish", "dr1", "dr 1", "tv2", "kanal 4"],
    "FI": ["finland", "finnish", "yle", "yle1", "mtv3", "nelonen"],
    "PL": ["poland", "polish", "tvp", "tvp1", "polsat", "tvn", "tvn24"],
    "CZ": ["czech", "czechia", "ct1", "ct 1", "nova", "prima"],
    "HU": ["hungary", "hungarian", "m1", "rtl", "tv2", "duna"],
    "RO": ["romania", "romanian", "tvr", "tvr1", "antena", "pro tv", "protv"],
    "GR": ["greece", "greek", "ert", "ert1", "mega", "ant1", "skai"],
    "RU": ["russia", "russian", "россия", "rt", "rtr", "первый", "sts", "ntv", "russia today"],
    "UA": ["ukraine", "ukrainian", "1+1", "ictv", "suspilne", "inter tv"],
    "IE": ["ireland", "irish", "rte", "rte1", "rte 1", "rte2", "tg4", "virgin media"],
    "IS": ["iceland", "icelandic", "ruv", "stod 2", "stod2"],
    "AT": ["austria", "austrian", "orf", "orf1", "orf 1", "atv", "puls 4"],
    "CH": ["switzerland", "swiss", "srf", "srf1", "rts", "rsi", "teleclub"],
    "HR": ["croatia", "croatian", "htv", "hrt", "novatv", "nova tv"],
    "RS": ["serbia", "serbian", "rts", "rts1", "pink", "b92"],
    "BG": ["bulgaria", "bulgarian", "bnt", "bnt1", "btv", "nova tv"],
    "AE": ["uae", "emirates", "dubai", "abu dhabi", "al jazeera", "mbc", "rotana"],
    "SA": ["saudi", "saudi arabia", "mbc", "rotana", "al arabiya", "al jazeera"],
    "IL": ["israel", "israeli", "kan", "keshet", "reshet", "channel 10", "i24"],
    "TR": ["turkey", "turkish", "trt", "trt1", "atv", "kanal d", "show tv", "star tv", "fox turkiye"],
    "SG": ["singapore", "singaporean", "mediacorp", "channel 5", "channel 8", "channelnewsasia", "cna"],
    "MY": ["malaysia", "malaysian", "astro", "rtm", "tv3", "8tv", "ntv7"],
    "TH": ["thailand", "thai", "thai tv", "true vision", "thairath", "channel 3", "workpoint", "bbtv"],
    "VN": ["vietnam", "vietnamese", "vtv", "vtv1", "vtv3", "htv", "thvl", "viettel"],
    "PH": ["philippines", "filipino", "abs-cbn", "abs cbn", "gma", "gma network", "tv5", "ptv", "anc"],
    "ID": ["indonesia", "indonesian", "tvri", "mnctv", "indosiar", "sctv", "antv", "trans tv", "metrotv"],
    "IN": ["india", "indian", "dd national", "star plus", "zeetv", "sony", "colors", "sun tv", "aaJ tak", "ndtv"],
    "PK": ["pakistan", "pakistani", "ptv", "geo tv", "ary", "hum tv", "express", "dunya"],
    "BD": ["bangladesh", "bangladeshi", "btv", "channel i", "n tv", "ekushey"],
    "LK": ["sri lanka", "srilankan", "slrc", "sirasa", "derana", "hiru"],
    "AU": ["australia", "australian", "abc australia", "abc news", "seven", "nine", "ten", "sbs", "foxtel", "optus"],
    "NZ": ["new zealand", "nz", "tvnz", "tv nz", "three", "maori tv", "sky nz"],
    "BR": ["brazil", "brazilian", "globo", "globo news", "record", "sbt", "band", "rede tv"],
    "AR": ["argentina", "argentinian", "telefe", "eltrece", "el trece", "america tv", "c5n", "cronica"],
    "CL": ["chile", "chilean", "tvn", "chilevision", "chilevision", "mega", "canal 13", "la red"],
    "CO": ["colombia", "colombian", "caracol", "rtc", "rcn", "canal uno", "citytv"],
    "PE": ["peru", "peruvian", "latina", "america television", "panamericana", "atv"],
    "MX": ["mexico", "mexican", "televisa", "las estrellas", "azteca", "azteca 7", "imagen tv", "canal 5"],
    "CA": ["canada", "canadian", "cbc", "cbc news", "ctv", "global", "citytv", "sportsnet", "tsn", "tva", "radio-canada"],
    "ZA": ["south africa", "sabc", "sabc1", "etv", "dstv", "supersport", "multichoice"],
    "EG": ["egypt", "egyptian", "ertu", "on e", "mbc masr", "cbc", "al jazeera mubasher"],
    "NG": ["nigeria", "nigerian", "aite", "ait", "nigerian television", "channelstv", "channels tv", "tv continental"],
    "MA": ["morocco", "moroccan", "2m", "al aoula", "medi1", "arriadia"],
    "KE": ["kenya", "kenyan", "ktn", "citizen tv", "ntv kenya", "kbc"],
}

# 无法识别时使用的兜底代码
UNKNOWN_COUNTRY = "ZZ"

# 用于从 URL 域名/TLD 推断国家的后缀映射
TLD_COUNTRY_MAP: Dict[str, str] = {
    "cn": "CN", "hk": "HK", "mo": "MO", "tw": "TW", "jp": "JP", "kr": "KR",
    "sg": "SG", "my": "MY", "th": "TH", "vn": "VN", "ph": "PH", "id": "ID",
    "in": "IN", "pk": "PK", "bd": "BD", "lk": "LK", "np": "NP", "mm": "MM",
    "ae": "AE", "sa": "SA", "il": "IL", "tr": "TR", "ir": "IR", "qa": "QA",
    "kw": "KW", "om": "OM", "bh": "BH", "lb": "LB", "jo": "JO",
    "uk": "GB", "gb": "GB", "fr": "FR", "de": "DE", "it": "IT", "es": "ES",
    "pt": "PT", "nl": "NL", "be": "BE", "ch": "CH", "at": "AT", "se": "SE",
    "no": "NO", "dk": "DK", "fi": "FI", "pl": "PL", "cz": "CZ", "sk": "SK",
    "hu": "HU", "ro": "RO", "bg": "BG", "gr": "GR", "ru": "RU", "ua": "UA",
    "ie": "IE", "is": "IS", "ee": "EE", "lv": "LV", "lt": "LT", "hr": "HR",
    "rs": "RS", "si": "SI",
    "us": "US", "ca": "CA", "mx": "MX",
    "br": "BR", "ar": "AR", "cl": "CL", "co": "CO", "pe": "PE", "ve": "VE",
    "uy": "UY", "py": "PY", "ec": "EC", "bo": "BO",
    "au": "AU", "nz": "NZ",
    "za": "ZA", "eg": "EG", "ng": "NG", "ma": "MA", "ke": "KE", "gh": "GH",
}


def get_country(code: str) -> Optional[dict]:
    """获取国家信息"""
    return COUNTRIES.get(code.upper())


def get_country_name_zh(code: str) -> str:
    """获取中文名"""
    info = COUNTRIES.get(code.upper(), {})
    return info.get("zh", code.upper())


def get_country_name_en(code: str) -> str:
    """获取英文名"""
    info = COUNTRIES.get(code.upper(), {})
    return info.get("en", code.upper())


def get_all_codes() -> list:
    """获取所有国家代码"""
    return sorted(COUNTRIES.keys())


def get_region_codes(region: str) -> list:
    """按大区获取国家代码"""
    return sorted([c for c, info in COUNTRIES.items() if info.get("region") == region])
