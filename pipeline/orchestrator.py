"""
管线编排器

将 Sources → Parser → Normalizer → Deduplicator → Classifier → IPDetector
          → Validator → SpeedTester → Ranker 串成完整流水线。

输入: 原始频道 dict 列表（来自 scrapers）
输出: 经过验证、分类、评分、排序的 Channel 列表
"""
import time
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import Channel
from countries import get_country, get_country_name_en, get_country_name_zh, UNKNOWN_COUNTRY
from pipeline.normalizer import normalize_name, is_valid_name, normalize_group
from pipeline.deduplicator import _channel_key
from pipeline.classifier import classify_country
from pipeline.ip_detector import detect_ip_version
from pipeline.validator import validate_stream
from pipeline.speed_tester import measure_speed
from pipeline.ranker import score_stream

from config import (
    HEALTH_CHECK_TIMEOUT_SECONDS,
    GITHUB_RAW_PROXY, ENABLE_SPEED_TEST, MIN_SPEED_KBPS,
    ENABLE_STREAM_VALIDATION, IP_TYPE_PREFER, SCORE_WEIGHTS,
    PIPELINE_MAX_SECONDS, PIPELINE_MAX_WORKERS,
)


class PipelineConfig:
    """管线配置（可覆盖）"""
    def __init__(self):
        self.proxy = GITHUB_RAW_PROXY
        self.enable_speed_test = ENABLE_SPEED_TEST
        self.min_speed_kbps = MIN_SPEED_KBPS
        self.enable_validation = ENABLE_STREAM_VALIDATION
        self.ip_type_prefer = IP_TYPE_PREFER
        self.score_weights = SCORE_WEIGHTS
        self.timeout = HEALTH_CHECK_TIMEOUT_SECONDS
        self.max_workers = PIPELINE_MAX_WORKERS
        self.max_seconds = PIPELINE_MAX_SECONDS


def apply_proxy(url: str, proxy: str = "") -> str:
    """为 raw.githubusercontent.com 应用国内代理前缀"""
    if not proxy:
        return url
    if "raw.githubusercontent.com" in url and not url.startswith(proxy):
        return proxy + url
    return url


def raw_to_channel(raw: dict) -> Optional[Channel]:
    """原始 dict → Channel（含分类/标准化，不含验证）"""
    name = (raw.get("name") or "").strip()
    url = (raw.get("url") or "").strip()
    if not name or not url or not is_valid_name(name):
        return None

    group = normalize_group(raw.get("group") or "")
    region = raw.get("region") or ""
    source_region = raw.get("source_region") or region

    # 国家/地区分类
    country_code = classify_country(name=name, group=group, url=url,
                                    source_region=source_region)

    ch = Channel(
        name=normalize_name(name),
        original_name=name,
        url=url,
        group=group,
        region=region or "international",
        country_code=country_code,
        country_name_en=get_country_name_en(country_code),
        country_name_zh=get_country_name_zh(country_code),
        continent=(get_country(country_code) or {}).get("region", ""),
        ip_version=detect_ip_version(url),
        logo=raw.get("logo") or "",
        tvg_id=raw.get("tvg_id") or "",
        kodi_props=raw.get("kodi_props") or "",
        source=raw.get("source") or "",
        is_active=True,
    )
    return ch


def _validate_one(ch: Channel, cfg: PipelineConfig) -> Channel:
    """验证单个频道（线程安全）"""
    url = apply_proxy(ch.url, cfg.proxy)
    # 1. 流验证
    vres = validate_stream(url, timeout=cfg.timeout, check_hls=True)
    if not vres["ok"]:
        ch.is_active = False
        ch.response_time_ms = vres["response_time_ms"]
        ch.score = score_stream(False, ip_version=ch.ip_version,
                                response_time_ms=vres["response_time_ms"],
                                weights=cfg.score_weights)["score"]
        return ch

    ch.is_active = True
    ch.response_time_ms = vres["response_time_ms"]
    ch.last_checked = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 2. 测速（可选）
    speed_kbps = 0.0
    if cfg.enable_speed_test:
        sres = measure_speed(url, timeout=cfg.timeout)
        speed_kbps = sres.get("speed_kbps", 0.0)
        ch.speed_kbps = speed_kbps

    # 3. IPv4 优先策略：仅当配置为 ipv4 且该源是纯 IPv6 时降低优先级（不删除）
    if cfg.ip_type_prefer == "ipv4" and ch.ip_version == "ipv6":
        ch.score -= 20  # 仅 IPv6 源降权，但仍保留为备用

    # 4. 综合评分
    score = score_stream(
        ok=True,
        ip_version=ch.ip_version,
        response_time_ms=vres["response_time_ms"],
        speed_kbps=speed_kbps if speed_kbps > 0 else None,
        mainland_ok=None,
        weights=cfg.score_weights,
    )["score"]
    ch.score += score

    # 5. 最低速度过滤
    if cfg.enable_speed_test and speed_kbps > 0 and speed_kbps < cfg.min_speed_kbps:
        ch.is_active = False

    return ch


def validate_channels(channels: List[Channel], cfg: PipelineConfig = None) -> List[Channel]:
    """并发验证频道列表"""
    cfg = cfg or PipelineConfig()
    if not cfg.enable_validation:
        return channels

    total = len(channels)
    done = 0
    results: List[Channel] = []
    collected: set = set()  # 已处理的 future
    start_time = time.time()
    print(f"  [验证] 开始验证 {total} 个频道（并发 {cfg.max_workers}）...")
    executor = ThreadPoolExecutor(max_workers=cfg.max_workers)
    try:
        futures = {executor.submit(_validate_one, ch, cfg): ch for ch in channels}
        try:
            # as_completed 带 timeout：若单个 future 卡死，此处抛 TimeoutError
            iterator = as_completed(futures, timeout=(cfg.max_seconds if cfg.max_seconds and cfg.max_seconds > 0 else None))
            for fut in iterator:
                collected.add(fut)
                done += 1
                try:
                    results.append(fut.result())
                except Exception:
                    results.append(futures[fut])
                if done % 100 == 0 or done == total:
                    active = sum(1 for r in results if r.is_active)
                    print(f"  [验证] 进度 {done}/{total}（可用 {active}）")
        except TimeoutError:
            # 总超时：只补收集未处理的 future
            for f, ch in futures.items():
                if f in collected:
                    continue
                if f.done():
                    try:
                        results.append(f.result())
                    except Exception:
                        results.append(ch)
                else:
                    results.append(ch)  # 未完成视为可用
            print(f"  [验证] 超过 {cfg.max_seconds}s，跳过剩余验证，保留 {len(futures)} 个频道")
    finally:
        # 不等待未完成任务，立即释放（避免卡死）
        executor.shutdown(wait=False, cancel_futures=True)
    return results


def rank_and_sort(channels: List[Channel]) -> List[Channel]:
    """按国家/地区 → 评分排序"""
    def sort_key(ch: Channel):
        # 未知国家排最后
        country_rank = 0 if ch.country_code == UNKNOWN_COUNTRY else 1
        return (country_rank, ch.country_code, -ch.score, ch.name)
    return sorted(channels, key=sort_key)


def run_pipeline(raw_channels: List[dict], cfg: PipelineConfig = None) -> List[Channel]:
    """
    完整管线入口。
    返回经过分类、去重（含同频道多源合并）、验证、评分、排序的 Channel 列表。
    """
    cfg = cfg or PipelineConfig()
    t0 = time.time()

    # 1. Normalize + Classify
    channels = []
    seen_urls = set()
    for raw in raw_channels:
        ch = raw_to_channel(raw)
        if not ch:
            continue
        # 2. URL 去重：用原始 URL（去空白/fragment）精确去重，
        #    保留 token 参数差异（不同 token = 不同源，供多源合并）
        raw_url = (ch.url or "").strip().split("#")[0]
        if raw_url in seen_urls:
            continue
        seen_urls.add(raw_url)
        channels.append(ch)

    print(f"  [Pipeline] 标准化+分类+去重: {len(channels)} 频道 ({time.time()-t0:.1f}s)")

    # 3. 验证 + 测速 + 评分（先验证全部源，合并时才能按真实评分选主源）
    if cfg.enable_validation:
        t1 = time.time()
        channels = validate_channels(channels, cfg)
        active = sum(1 for c in channels if c.is_active)
        print(f"  [Pipeline] 验证: {active}/{len(channels)} 可用 ({time.time()-t1:.1f}s)")

    # 4. 同频道多源合并：主源选验证后评分最高且可用的源（失效源排最后）
    name_groups: dict = {}
    for ch in channels:
        nk = _channel_key(ch.name)
        name_groups.setdefault(nk, []).append(ch)
    merged = []
    for nk, items in name_groups.items():
        # 主源选可用且评分最高；全部失效时保留第一个（输出阶段会过滤）
        items.sort(key=lambda c: (not c.is_active, -c.score, c.response_time_ms))
        primary = items[0]
        primary.sources = [{
            "url": c.url, "source": c.source,
            "score": c.score, "response_time_ms": c.response_time_ms,
            "ip_version": c.ip_version,
        } for c in items]
        primary.source_count = len(items)
        merged.append(primary)
    channels = merged

    # 5. 排序
    channels = rank_and_sort(channels)
    print(f"  [Pipeline] 完成，共 {len(channels)} 频道 ({time.time()-t0:.1f}s 总计)")
    return channels
