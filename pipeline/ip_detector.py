"""
IPv4/IPv6 协议识别器

识别直播源 URL 的协议类型：
- ipv4: 直接 IPv4 地址
- ipv6: 直接 IPv6 地址
- domain: 域名（可能解析 IPv4/IPv6）
- dual: 域名同时支持 IPv4/IPv6
"""
import re
import socket
from typing import Optional
from urllib.parse import urlparse

_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)
_IPV6_RE = re.compile(r"^[0-9a-fA-F:]+$")


def is_ipv4(host: str) -> bool:
    return bool(_IPV4_RE.match(host))


def is_ipv6(host: str) -> bool:
    if not _IPV6_RE.match(host):
        return False
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except (OSError, ValueError):
        return False


def get_host(url: str) -> str:
    """提取 URL 主机名"""
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def detect_ip_version(url: str) -> str:
    """
    识别协议类型：
    - 'ipv4'  直接 IPv4
    - 'ipv6'  直接 IPv6
    - 'domain' 域名（不确定）
    """
    host = get_host(url)
    if not host:
        return "unknown"
    # 去掉 IPv6 的方括号
    host = host.strip("[]")
    if is_ipv4(host):
        return "ipv4"
    if is_ipv6(host):
        return "ipv6"
    return "domain"


def resolve_domain(host: str, timeout: float = 3.0) -> dict:
    """
    解析域名，返回：
    {"host": ..., "has_ipv4": bool, "has_ipv6": bool, "ips": [...]}
    """
    if not host:
        return {"host": host, "has_ipv4": False, "has_ipv6": False, "ips": []}
    host = host.strip("[]")
    if is_ipv4(host):
        return {"host": host, "has_ipv4": True, "has_ipv6": False, "ips": [host]}
    if is_ipv6(host):
        return {"host": host, "has_ipv4": False, "has_ipv6": True, "ips": [host]}
    try:
        infos = socket.getaddrinfo(host, None, 0, socket.SOCK_STREAM)
        ips = list({info[4][0] for info in infos})
        has_ipv4 = any(is_ipv4(ip) for ip in ips)
        has_ipv6 = any(is_ipv6(ip) for ip in ips)
        return {"host": host, "has_ipv4": has_ipv4, "has_ipv6": has_ipv6, "ips": ips}
    except socket.gaierror:
        return {"host": host, "has_ipv4": False, "has_ipv6": False, "ips": []}


def ip_priority(ip_version: str) -> int:
    """
    返回 IPv4 优先级分数（越高越优先）：
    ipv4 直连 = 100
    domain+ipv4 = 80
    dual (ipv4+ipv6) = 60
    domain 未知 = 40
    ipv6 = 20
    unknown = 0
    """
    return {
        "ipv4": 100,
        "domain_ipv4": 80,
        "dual": 60,
        "domain": 40,
        "ipv6": 20,
        "unknown": 0,
    }.get(ip_version, 0)
