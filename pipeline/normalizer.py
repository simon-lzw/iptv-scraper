"""
频道名/分组标准化器

统一频道名称格式，去除多余空格，规范化常见变体，但不过度修改原始名称。
保留 original_name 与 normalized_name。
"""
import re
from typing import Optional

# 常见频道名变体 → 标准名（精确匹配）
EXACT_OVERRIDES = {
    "CCTV1": "CCTV-1",
    "CCTV2": "CCTV-2",
    "CCTV3": "CCTV-3",
    "CCTV4": "CCTV-4",
    "CCTV5": "CCTV-5",
    "CCTV6": "CCTV-6",
    "CCTV7": "CCTV-7",
    "CCTV8": "CCTV-8",
    "CCTV9": "CCTV-9",
    "CCTV10": "CCTV-10",
    "CCTV11": "CCTV-11",
    "CCTV12": "CCTV-12",
    "CCTV13": "CCTV-13",
    "CCTV14": "CCTV-14",
    "CCTV15": "CCTV-15",
    "CCTV16": "CCTV-16",
    "CCTV17": "CCTV-17",
}

# 正则变体（顺序重要，先匹配更具体的）
_PATTERNS = [
    (re.compile(r"^CCTV\s*(\d+)$", re.I), r"CCTV-\1"),
    (re.compile(r"^CCTV\s*(\d+)\s*综合$", re.I), r"CCTV-\1 综合"),
    (re.compile(r"^CCTV\s*(\d+)\s*HD$", re.I), r"CCTV-\1 HD"),
    (re.compile(r"\s{2,}"), " "),
]


def normalize_name(name: str) -> str:
    """标准化频道名，返回 (original, normalized) 的 normalized 部分"""
    if not name:
        return ""
    name = name.strip()
    # 去除两端括号标记（如 [HD]、[超清] 等保留在名称后的常见后缀清理不执行）
    for pattern, repl in _PATTERNS:
        name = pattern.sub(repl, name)
    # 统一空
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def normalize_group(group: str) -> str:
    """标准化分组名：清理多余空格，去除常见噪音"""
    if not group:
        return ""
    group = group.strip()
    group = re.sub(r"\s+", " ", group)
    # 去除常见分组噪音后缀
    group = re.sub(r"^(【|\[)(.+?)(】|\])$", r"\2", group)
    return group


def is_valid_name(name: str) -> bool:
    """检查频道名是否有效（过滤纯数字、纯标点等）"""
    if not name or not name.strip():
        return False
    # 纯标点/纯数字视为无效
    stripped = re.sub(r"[\s\-_（）()\[\]【】:：.,，。!！?？/\\|&]", "", name)
    if not stripped:
        return False
    if stripped.isdigit():
        return False
    return True


def get_sort_key(name: str) -> str:
    """获取排序键（拼音/数字优先）"""
    name = name.strip().lower()
    # 数字开头的排最前
    if re.match(r"^\d", name):
        return "0" + name
    # 英文开头
    if re.match(r"^[a-z]", name):
        return "1" + name
    return "2" + name
