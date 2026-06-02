"""
HTTP 服务 — 向电视提供 M3U 播放列表 + 管理 API

提供:
  - GET /playlist.m3u  → M3U 播放列表
  - GET /api/status    → 系统状态
  - GET /api/channels  → 频道列表 (JSON)
  - POST /api/scrape   → 手动触发搜刮
  - POST /api/heal     → 手动触发修复

电视播放器设置: http://<你的IP>:5000/playlist.m3u
"""
import json
import sys
from pathlib import Path
from typing import Optional, Dict

# Windows GBK 终端兼容
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

from config import PORT, HOST, M3U_OUTPUT_PATH


class M3UServer:
    """Flask HTTP 服务"""

    def __init__(self, db, m3u_generator, scheduler):
        self.db = db
        self.m3u = m3u_generator
        self.scheduler = scheduler  # 调度器引用，用于手动触发
        self.app = Flask(__name__)
        CORS(self.app)

        self._register_routes()

    def _register_routes(self):
        app = self.app

        @app.route("/playlist_by_protocol.m3u")
        def get_playlist_by_protocol():
            """M3U 播放列表 (按协议分组: IPv6/IPv4/RTP)"""
            channels = self.db.get_active_channels()
            if not channels:
                return Response("# 暂无频道\n", mimetype="application/x-mpegurl")
            m3u_content = self.m3u.generate_grouped_by_protocol(channels)
            return Response(
                m3u_content,
                mimetype="application/x-mpegurl",
                headers={
                    "Content-Disposition": 'inline; filename="playlist_by_protocol.m3u"',
                    "Access-Control-Allow-Origin": "*",
                }
            )

        @app.route("/playlist.m3u")
        def get_playlist():
            """提供 M3U 播放列表 — 优先返回缓存文件，否则实时生成"""
            # 尝试返回已生成的 M3U 文件
            m3u_path = self.m3u.get_output_path()
            if m3u_path.exists():
                return send_file(
                    str(m3u_path),
                    mimetype="application/x-mpegurl",
                    as_attachment=False,
                )

            # 缓存不存在则实时生成
            channels = self.db.get_active_channels()
            if not channels:
                return Response("# 暂无频道\n", mimetype="application/x-mpegurl")
            m3u_content = self.m3u.generate(channels)
            return Response(
                m3u_content,
                mimetype="application/x-mpegurl",
                headers={
                    "Content-Disposition": 'inline; filename="playlist.m3u"',
                    "Access-Control-Allow-Origin": "*",
                }
            )

        @app.route("/api/status")
        def api_status():
            """系统状态"""
            stats = self.db.count_channels()
            return jsonify({
                "status": "running",
                "channels": stats,
            })

        @app.route("/api/channels")
        def api_channels():
            """频道列表"""
            region = request.args.get("region")
            if region:
                channels = self.db.get_channels_by_region(region)
            else:
                channels = self.db.get_all_channels()

            return jsonify({
                "total": len(channels),
                "channels": [
                    {
                        "id": ch.id,
                        "name": ch.name,
                        "url": ch.url,
                        "group": ch.group,
                        "region": ch.region,
                        "is_active": ch.is_active,
                        "fail_count": ch.fail_count,
                        "response_time_ms": ch.response_time_ms,
                        "source": ch.source,
                    }
                    for ch in channels
                ]
            })

        @app.route("/api/channels/inactive")
        def api_inactive():
            """失效频道"""
            channels = self.db.get_inactive_channels()
            return jsonify({
                "total": len(channels),
                "channels": [
                    {
                        "id": ch.id,
                        "name": ch.name,
                        "url": ch.url,
                        "fail_count": ch.fail_count,
                    }
                    for ch in channels
                ]
            })

        @app.route("/api/scrape", methods=["POST"])
        def api_scrape():
            """手动触发搜刮"""
            if self.scheduler:
                asyncio_run(self.scheduler.run_scrape())
                return jsonify({"status": "ok", "message": "搜刮完成"})
            return jsonify({"status": "error", "message": "调度器未就绪"}), 500

        @app.route("/api/heal", methods=["POST"])
        def api_heal():
            """手动触发修复"""
            if self.scheduler:
                asyncio_run(self.scheduler.run_auto_heal())
                return jsonify({"status": "ok", "message": "修复完成"})
            return jsonify({"status": "error", "message": "调度器未就绪"}), 500

        @app.route("/api/scrape/history")
        def api_scrape_history():
            """搜刮历史"""
            records = self.db.get_recent_scrapes(20)
            return jsonify({
                "records": [
                    {
                        "channel_name": r.channel_name,
                        "source": r.source_website,
                        "success": r.success,
                        "time": r.checked_at,
                    }
                    for r in records
                ]
            })

        @app.route("/")
        def index():
            """Web 管理页面"""
            stats = self.db.count_channels()
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>IPTV 直播源管理器</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: #eee; }}
                    h1, h2 {{ color: #4CAF50; }}
                    .card {{ background: #2a2a2a; border-radius: 8px; padding: 16px; margin: 10px 0; }}
                    .stat {{ display: inline-block; margin: 0 20px; text-align: center; }}
                    .stat-value {{ font-size: 2em; font-weight: bold; }}
                    .stat-label {{ color: #888; }}
                    .btn {{ display: inline-block; background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; margin: 5px; }}
                    .btn:hover {{ background: #45a049; }}
                    .btn-danger {{ background: #f44336; }}
                    .btn-danger:hover {{ background: #da190b; }}
                    .url-box {{ background: #333; border: 1px solid #555; padding: 12px; border-radius: 4px; font-size: 1.2em; text-align: center; margin: 10px 0; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #444; }}
                    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }}
                    .badge-active {{ background: #4CAF50; }}
                    .badge-inactive {{ background: #f44336; }}
                </style>
            </head>
            <body>
                <h1>📺 IPTV 直播源管理器</h1>

                <div class="card">
                    <h2>系统状态</h2>
                    <div class="stat">
                        <div class="stat-value">{stats['total']}</div>
                        <div class="stat-label">总频道</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color:#4CAF50">{stats['active']}</div>
                        <div class="stat-label">活跃</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color:#f44336">{stats['inactive']}</div>
                        <div class="stat-label">失效</div>
                    </div>
                </div>

                <div class="card">
                    <h2>播放列表地址</h2>
                    <div class="url-box">
                        <code>http://{request.host}/playlist.m3u</code>
                    </div>
                    <p style="color:#888; text-align:center;">在 TiviMate / VLC 中添加此链接即可播放</p>
                </div>

                <div class="card">
                    <h2>操作</h2>
                    <button class="btn" onclick="triggerScrape()">🔄 手动搜刮</button>
                    <button class="btn" onclick="triggerHeal()">🔧 修复失效源</button>
                    <div id="result" style="margin-top:10px;"></div>
                </div>

                <div class="card">
                    <h2>频道概览</h2>
                    <table>
                        <tr><th>区域</th><th>分组</th><th>频道数</th><th>活跃</th></tr>
                        {self._render_channel_summary()}
                    </table>
                </div>

                <script>
                    async function triggerScrape() {{
                        document.getElementById('result').innerHTML = '⏳ 搜刮中...';
                        const r = await fetch('/api/scrape', {{method:'POST'}});
                        const d = await r.json();
                        document.getElementById('result').innerHTML = '✅ ' + d.message;
                        setTimeout(() => location.reload(), 2000);
                    }}
                    async function triggerHeal() {{
                        document.getElementById('result').innerHTML = '⏳ 修复中...';
                        const r = await fetch('/api/heal', {{method:'POST'}});
                        const d = await r.json();
                        document.getElementById('result').innerHTML = '✅ ' + d.message;
                        setTimeout(() => location.reload(), 2000);
                    }}
                </script>
            </body>
            </html>
            """

        @app.route("/channels")
        def channels_page():
            """频道列表页面"""
            channels = self.db.get_all_channels()
            rows = ""
            for ch in channels:
                badge = "badge-active" if ch.is_active else "badge-inactive"
                status_text = "活跃" if ch.is_active else f"失效(×{ch.fail_count})"
                rows += f"""<tr>
                    <td>{ch.name}</td>
                    <td>{ch.group}</td>
                    <td>{ch.region}</td>
                    <td><span class="badge {badge}">{status_text}</span></td>
                    <td style="font-size:0.8em;color:#888;max-width:300px;overflow:hidden;text-overflow:ellipsis;">{ch.url[:60]}…</td>
                </tr>"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>频道列表 - IPTV 管理器</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: #eee; }}
                    h1 {{ color: #4CAF50; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #444; }}
                    th {{ position: sticky; top: 0; background: #1a1a1a; }}
                    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }}
                    .badge-active {{ background: #4CAF50; }}
                    .badge-inactive {{ background: #f44336; }}
                    a {{ color: #4CAF50; text-decoration: none; }}
                </style>
            </head>
            <body>
                <h1>📺 频道列表</h1>
                <p><a href="/">← 返回首页</a> | 共 {len(channels)} 个频道</p>
                <table>
                    <tr><th>名称</th><th>分组</th><th>区域</th><th>状态</th><th>URL</th></tr>
                    {rows}
                </table>
            </body>
            </html>
            """

    def _render_channel_summary(self) -> str:
        """生成频道概览表格 HTML"""
        channels = self.db.get_all_channels()
        from collections import Counter
        region_count = Counter()
        region_active = Counter()
        group_summary: Dict[str, Counter] = {}

        for ch in channels:
            region_count[ch.region] += 1
            if ch.is_active:
                region_active[ch.region] += 1
            key = f"{ch.region}|{ch.group}"
            if key not in group_summary:
                group_summary[key] = Counter()
            group_summary[key]["total"] += 1
            if ch.is_active:
                group_summary[key]["active"] += 1

        # 按区域汇总
        rows = ""
        for region in ["mainland", "hongkong", "macau", "taiwan"]:
            label = {"mainland": "中国大陆", "hongkong": "香港", "macau": "澳门", "taiwan": "台湾"}.get(region, region)
            total = region_count.get(region, 0)
            active = region_active.get(region, 0)
            if total == 0:
                continue
            pct = f"{int(active/total*100)}%" if total > 0 else "0%"
            rows += f"<tr><td>{label}</td><td>-</td><td>{total}</td><td style='color:#4CAF50'>{active} ({pct})</td></tr>"

        return rows

    def start(self):
        """启动 HTTP 服务"""
        print(f"\n  [HTTP] 服务启动: http://{HOST}:{PORT}")
        print(f"  [TV] 播放器添加: http://<你的IP>:{PORT}/playlist.m3u")
        print(f"  [WEB] 管理页面: http://<你的IP>:{PORT}/\n")
        self.app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def asyncio_run(coro):
    """同步调用异步函数"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(coro)
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)
