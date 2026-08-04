"""
测速器

- 测量下载速度（读取有限字节）
- 测量首字节延迟
- 计算稳定性（多次采样）
"""
import time
from typing import Optional
import requests
from config import USER_AGENT


def measure_speed(url: str, sample_bytes: int = 262144,
                  timeout: int = 8, samples: int = 1) -> dict:
    """
    测量直播源下载速度。
    返回: {"ok": bool, "speed_kbps": float, "first_byte_ms": int,
           "total_ms": int, "bytes": int, "error": str}
    """
    result = {"ok": False, "speed_kbps": 0.0, "first_byte_ms": 0,
              "total_ms": 0, "bytes": 0, "error": ""}
    if not url or not url.startswith(("http://", "https://")):
        result["error"] = "unsupported protocol"
        return result

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Range": "bytes=0-1048575",  # 尝试请求 1MB 范围
    }

    try:
        start = time.monotonic()
        with requests.get(url, headers=headers, timeout=timeout,
                          allow_redirects=True, stream=True) as resp:
            if resp.status_code >= 400:
                result["error"] = f"HTTP {resp.status_code}"
                return result
            first_byte_time = time.monotonic()
            result["first_byte_ms"] = int((first_byte_time - start) * 1000)
            bytes_read = 0
            for chunk in resp.iter_content(chunk_size=16384):
                bytes_read += len(chunk)
                if bytes_read >= sample_bytes:
                    break
            total_ms = int((time.monotonic() - start) * 1000)
            result["total_ms"] = total_ms
            result["bytes"] = bytes_read
            if total_ms > 0 and bytes_read > 0:
                # KB/s = bytes/1024 / (ms/1000)
                result["speed_kbps"] = round(bytes_read / 1024.0 / (total_ms / 1000.0), 1)
            result["ok"] = True
            return result
    except requests.exceptions.Timeout:
        result["error"] = "timeout"
        return result
    except requests.exceptions.ConnectionError:
        result["error"] = "connection error"
        return result
    except Exception as e:
        result["error"] = str(e)[:80]
        return result


def measure_stability(url: str, runs: int = 3, timeout: int = 5) -> dict:
    """
    多次采样测量稳定性。
    返回: {"ok": bool, "success_count": int, "failure_rate": float,
           "avg_speed_kbps": float, "successes": list}
    """
    results = []
    for _ in range(runs):
        r = measure_speed(url, sample_bytes=65536, timeout=timeout, samples=1)
        results.append(r)
        if not r["ok"]:
            break
    ok_count = sum(1 for r in results if r["ok"])
    total = len(results)
    speeds = [r["speed_kbps"] for r in results if r["ok"]]
    return {
        "ok": ok_count > 0,
        "success_count": ok_count,
        "total_runs": total,
        "failure_rate": round((total - ok_count) / total, 2) if total else 1.0,
        "avg_speed_kbps": round(sum(speeds) / len(speeds), 1) if speeds else 0.0,
        "successes": results,
    }
