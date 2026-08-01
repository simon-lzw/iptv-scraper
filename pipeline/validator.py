"""
直播源有效性验证器

- HTTP/HTTPS: 状态码 + 重定向 + 响应时间
- HLS (.m3u8): 获取播放列表内容，检查是否为有效 HLS Playlist，
  并验证存在媒体分片（.ts / .m3u8 / fMP4）
- 不因单个失效源阻塞整体
"""
import time
from typing import Optional, Tuple
import requests
from config import USER_AGENT, HEALTH_CHECK_TIMEOUT_SECONDS

_HLS_MARKERS = ("#EXTM3U", "#EXT-X-STREAM-INF", "#EXTINF", "#EXT-X-MEDIA-SEQUENCE")
_TS_MARKERS = (".ts", "mpegts", "application/vnd.apple.mpegurl", "video/mp2t")
_SEGMENT_RE = None


def _headers():
    return {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def validate_stream(url: str, timeout: int = None,
                    check_hls: bool = True) -> dict:
    """
    验证直播源有效性。
    返回: {"ok": bool, "status": int, "response_time_ms": int,
           "redirect_count": int, "is_hls": bool, "has_segments": bool,
           "error": str, "content_type": str, "final_url": str}
    """
    timeout = timeout or HEALTH_CHECK_TIMEOUT_SECONDS
    result = {
        "ok": False, "status": 0, "response_time_ms": 0,
        "redirect_count": 0, "is_hls": False, "has_segments": False,
        "error": "", "content_type": "", "final_url": url,
    }
    if not url or not url.startswith(("http://", "https://")):
        result["error"] = "unsupported protocol"
        return result

    is_hls = url.lower().endswith(".m3u8") or "m3u8" in url.lower()
    result["is_hls"] = is_hls

    start = time.monotonic()
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout,
                            allow_redirects=True, stream=True)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        result["response_time_ms"] = elapsed_ms
        result["status"] = resp.status_code
        result["content_type"] = (resp.headers.get("Content-Type") or "").lower()
        result["final_url"] = resp.url
        result["redirect_count"] = len(resp.history)

        if resp.status_code >= 400:
            result["error"] = f"HTTP {resp.status_code}"
            resp.close()
            return result

        if is_hls and check_hls:
            # 读取部分内容判断 HLS playlist
            content = b""
            for chunk in resp.iter_content(chunk_size=4096):
                content += chunk
                if len(content) > 65536:  # 最多读 64KB
                    break
            resp.close()
            try:
                text = content.decode("utf-8", errors="replace")
            except Exception:
                text = ""
            result["is_hls"] = "#EXT" in text or "#EXTM3U" in text
            # 检查媒体分片
            has_seg = (
                ".ts" in text or ".m3u8" in text.lower()
                or "EXT-X-STREAM-INF" in text
                or "EXTINF" in text
                or any(m in result["content_type"] for m in _TS_MARKERS)
            )
            result["has_segments"] = has_seg
            if not has_seg:
                result["error"] = "HLS playlist without segments"
                return result
        else:
            resp.close()
            # 非 HLS：检查 content-type 是否像视频流
            ct = result["content_type"]
            if ct and ("video" not in ct and "mpegurl" not in ct
                       and "mp2t" not in ct and "octet-stream" not in ct
                       and "application/x-mpeg" not in ct
                       and "application/vnd.apple" not in ct
                       and ct != ""):
                # 纯 HTML 页面通常是无效源
                if "text/html" in ct:
                    result["error"] = "HTML content, not a stream"
                    return result

        result["ok"] = True
        return result
    except requests.exceptions.Timeout:
        result["error"] = "timeout"
        return result
    except requests.exceptions.SSLError:
        result["error"] = "ssl error"
        return result
    except requests.exceptions.ConnectionError:
        result["error"] = "connection error"
        return result
    except Exception as e:
        result["error"] = str(e)[:80]
        return result
