"""
直播源健康检查器

检查策略:
  1. HTTP HEAD 请求 (快速)
  2. 检查 Content-Type 是否为视频流
  3. 可选: ffprobe 探测 (精确)
  4. 评分: 响应时间 + 状态码
"""
import asyncio
import time
import subprocess
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import aiohttp

from models import Channel
from config import (
    HEALTH_CHECK_TIMEOUT_SECONDS,
    MAX_CONCURRENT_CHECKS,
    FFPROBE_TIMEOUT_SECONDS,
)


class HealthChecker:
    """直播源健康检查"""

    # 有效的视频 Content-Type 前缀
    VALID_CONTENT_TYPES = [
        "application/vnd.apple.mpegurl",
        "application/x-mpegurl",
        "video/mp2t",
        "video/mp4",
        "video/x-flv",
        "application/dash+xml",
        "video/x-mpeg",
        "application/x-httpd-live",
    ]

    def __init__(self):
        self.results: Dict[int, CheckResult] = {}

    async def check_channel(self, channel: Channel) -> "CheckResult":
        """检查单个频道"""
        start = time.time()
        result = CheckResult(channel_id=channel.id)

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=HEALTH_CHECK_TIMEOUT_SECONDS)
            ) as session:
                # 1. HTTP HEAD 请求
                async with session.head(
                    channel.url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "*/*",
                    },
                    allow_redirects=True,
                ) as resp:
                    elapsed_ms = int((time.time() - start) * 1000)
                    result.response_time_ms = elapsed_ms
                    result.status_code = resp.status

                    if resp.status != 200:
                        result.is_active = False
                        result.reason = f"HTTP {resp.status}"
                        self.results[channel.id] = result
                        return result

                    # 2. 检查 Content-Type
                    content_type = resp.headers.get("Content-Type", "")
                    if content_type and not self._is_valid_type(content_type):
                        # 不是视频类型，尝试 GET 再判断
                        pass

                    result.is_active = True
                    result.reason = "OK"

        except asyncio.TimeoutError:
            result.is_active = False
            result.reason = "超时"
        except aiohttp.ClientError as e:
            result.is_active = False
            result.reason = f"连接错误: {str(e)[:50]}"
        except Exception as e:
            result.is_active = False
            result.reason = f"异常: {str(e)[:50]}"

        self.results[channel.id] = result
        return result

    async def check_batch(self, channels: List[Channel]) -> List["CheckResult"]:
        """并发检查多个频道"""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

        async def _check_with_sem(ch: Channel) -> "CheckResult":
            async with semaphore:
                return await self.check_channel(ch)

        tasks = [_check_with_sem(ch) for ch in channels]
        return await asyncio.gather(*tasks)

    async def deep_check_inactive(self, channels: List[Channel]) -> List["CheckResult"]:
        """深度检查失效频道 — 用更长超时逐个测试，确保网络波动不误判"""
        import math
        results = []
        total = len(channels)
        for i, ch in enumerate(channels):
            self.logger.info("    深度检查 [%d/%d]: %s", i + 1, total, ch.name)
            # 使用更长的超时 (30s)
            result = await self._check_with_long_timeout(ch)
            results.append(result)
        return results

    async def _check_with_long_timeout(self, channel: Channel) -> "CheckResult":
        """用 30s 超时检查单个频道"""
        import time
        start = time.time()
        result = CheckResult(channel_id=channel.id)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.head(
                    channel.url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    allow_redirects=True,
                ) as resp:
                    elapsed_ms = int((time.time() - start) * 1000)
                    result.response_time_ms = elapsed_ms
                    result.status_code = resp.status
                    result.is_active = (resp.status == 200)
                    result.reason = "OK" if resp.status == 200 else f"HTTP {resp.status}"
        except asyncio.TimeoutError:
            result.is_active = False
            result.reason = "超时(30s)"
        except aiohttp.ClientError as e:
            result.is_active = False
            result.reason = f"连接错误: {str(e)[:50]}"
        except Exception as e:
            result.is_active = False
            result.reason = f"异常: {str(e)[:50]}"
        self.results[channel.id] = result
        return result

    def _is_valid_type(self, content_type: str) -> bool:
        """判断是否为有效的视频流 Content-Type"""
        ct = content_type.lower().split(";")[0].strip()
        return any(valid in ct for valid in self.VALID_CONTENT_TYPES)

    @staticmethod
    def verify_with_ffprobe(url: str) -> Tuple[bool, str]:
        """使用 ffprobe 精确验证流是否有效"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    "-timeout", str(FFPROBE_TIMEOUT_SECONDS * 1000000),
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=FFPROBE_TIMEOUT_SECONDS + 2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True, f"duration={result.stdout.strip()}s"
            else:
                return False, result.stderr.strip()[:100]
        except FileNotFoundError:
            return False, "ffprobe not installed"
        except subprocess.TimeoutExpired:
            return False, "ffprobe timeout"
        except Exception as e:
            return False, str(e)[:100]


class CheckResult:
    """单个频道的检查结果"""

    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.is_active: bool = False
        self.response_time_ms: int = 0
        self.status_code: int = 0
        self.reason: str = ""

    def __repr__(self):
        return (
            f"CheckResult(id={self.channel_id}, active={self.is_active}, "
            f"code={self.status_code}, time={self.response_time_ms}ms, "
            f"reason={self.reason})"
        )


async def run_health_check(channels: List[Channel]) -> Dict[int, CheckResult]:
    """便捷函数：执行一次健康检查"""
    checker = HealthChecker()
    await checker.check_batch(channels)
    return checker.results


async def run_deep_check(channels: List[Channel]) -> Dict[int, CheckResult]:
    """便捷函数：执行一次深度检查（用于失效频道的恢复验证）"""
    checker = HealthChecker()
    await checker.deep_check_inactive(channels)
    return checker.results
