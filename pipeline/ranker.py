"""
综合质量评分器

评分维度（权重可配置）：
- availability      可用性
- ipv4_priority     IPv4 优先级
- response_speed    响应速度
- download_speed    下载速度
- stability         稳定性
- mainland_access   中国大陆访问质量

score = Σ(w_i * s_i)，范围 0-100
"""
from typing import Optional, Tuple

# 默认评分权重（可配置，和为 1.0）
DEFAULT_WEIGHTS = {
    "availability": 0.30,
    "ipv4_priority": 0.20,
    "response_speed": 0.15,
    "download_speed": 0.15,
    "stability": 0.10,
    "mainland_access": 0.10,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def score_stream(ok: bool, ip_version: str = "unknown",
                 response_time_ms: Optional[int] = None,
                 speed_kbps: Optional[float] = None,
                 failure_rate: Optional[float] = None,
                 mainland_ok: Optional[bool] = None,
                 weights: Optional[dict] = None) -> dict:
    """
    计算直播源质量评分。
    返回: {"score": 0-100, "details": {...各维度得分...}}
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    # 归一化权重
    wsum = sum(w.values()) or 1.0
    w = {k: v / wsum for k, v in w.items()}

    # 1. 可用性
    availability = 1.0 if ok else 0.0

    # 2. IPv4 优先级
    ipv4_map = {
        "ipv4": 1.0, "domain_ipv4": 0.8, "dual": 0.6,
        "domain": 0.4, "ipv6": 0.2, "unknown": 0.0,
    }
    ipv4_score = ipv4_map.get(ip_version, 0.0)

    # 3. 响应速度 (<=300ms 满分, >=5000ms 0分)
    if response_time_ms is None:
        response_score = 0.5
    else:
        response_score = _clamp(1.0 - (response_time_ms - 300) / 4700.0)

    # 4. 下载速度 (>=5000 KB/s 满分, <=100 KB/s 0分)
    if speed_kbps is None:
        speed_score = 0.5
    else:
        speed_score = _clamp((speed_kbps - 100) / 4900.0)

    # 5. 稳定性
    if failure_rate is None:
        stability_score = 0.5
    else:
        stability_score = 1.0 - _clamp(failure_rate)

    # 6. 中国大陆访问质量
    if mainland_ok is None:
        mainland_score = 0.5
    else:
        mainland_score = 1.0 if mainland_ok else 0.0

    details = {
        "availability": round(availability, 3),
        "ipv4_priority": round(ipv4_score, 3),
        "response_speed": round(response_score, 3),
        "download_speed": round(speed_score, 3),
        "stability": round(stability_score, 3),
        "mainland_access": round(mainland_score, 3),
    }

    total = sum(w[k] * details[k] for k in details)
    return {
        "score": round(total * 100, 1),
        "details": details,
        "weights": w,
    }


def pick_best(channels: list, limit: int = 5) -> list:
    """从同频道多源中按评分选择最佳源（按配置 limit 保留前 N 个）"""
    scored = [c for c in channels if c.get("score", 0) > 0]
    scored.sort(key=lambda c: -c.get("score", 0))
    return scored[:limit]
