#!/usr/bin/env python3
"""
IPTV 直播源自动搜刮系统 — 主入口

功能:
  1. 定时搜刮各来源的直播源
  2. 健康检查 + 自动修复失效源
  3. 生成 M3U 播放列表供电视播放
  4. HTTP 管理界面

用法:
  python main.py              # 启动完整系统
  python main.py --scrape     # 仅执行一次搜刮
  python main.py --check      # 仅执行一次健康检查
  python main.py --server     # 仅启动 HTTP 服务
"""
import sys
import asyncio
import time
import argparse
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Windows GBK 终端兼容
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 日志配置：控制台输出 + 可选文件日志 (--log-file)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)

import schedule

from db import Database
from models import Channel, ScrapeRecord
from m3u_generator import M3UGenerator
from checker import HealthChecker, run_health_check
from server import M3UServer
from config import (
    HEALTH_CHECK_INTERVAL_MINUTES,
    SCRAPE_INTERVAL_HOURS,
    AUTO_HEAL_INTERVAL_MINUTES,
    GROUP_REGION_MAP,
)


class IPTVScheduler:
    """
    主调度器 — 管理搜刮、检查、修复、M3U 生成
    """

    def __init__(self):
        self.db = Database()
        self.m3u = M3UGenerator()
        self.checker = HealthChecker()
        self.scrapers = []  # 延迟初始化

    def _init_scrapers(self):
        """初始化搜刮器"""
        if not self.scrapers:
            from scrapers.github_sources import GitHubScraper
            from scrapers.web_sources import WebScraper
            self.scrapers = [
                GitHubScraper(),
                WebScraper(),
            ]

    # ─── 搜刮 ────────────────────────────────────────────────────────

    async def run_scrape(self):
        """执行一次全量搜刮"""
        print(f"\n{'='*50}")
        print(f"  🔍 开始搜刮直播源... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")

        self._init_scrapers()
        all_new = 0
        all_total = 0

        for scraper in self.scrapers:
            try:
                print(f"\n  使用 {type(scraper).__name__}:")
                channels_data = scraper.scrape()
                channels = self._dicts_to_channels(channels_data, scraper)
                all_total += len(channels)

                # 批量写入数据库
                self.db.add_channels_batch(channels)
                new_count = self._count_new_channels(channels)
                all_new += new_count

                # 记录搜刮日志
                for ch in channels:
                    record = ScrapeRecord(
                        channel_name=ch.name,
                        source_website=ch.source,
                        url_found=ch.url,
                        success=True,
                    )
                    self.db.add_scrape_record(record)

                print(f"  ✓ {type(scraper).__name__}: {len(channels)} 个频道 (新增 {new_count})")

            except Exception as e:
                print(f"  ✗ 搜刮失败 {type(scraper).__name__}: {e}")
                import traceback
                traceback.print_exc()

        # 分组修正
        self._fix_grouping()

        # 生成 M3U
        self._generate_m3u()

        print(f"\n{'='*50}")
        print(f"  ✅ 搜刮完成！总计 {all_total} 个频道，新增 {all_new} 个")
        print(f"{'='*50}")

        return all_total, all_new

    # ─── 健康检查 ───────────────────────────────────────────────────

    async def run_health_check(self):
        """执行健康检查"""
        print(f"\n  🏥 开始健康检查... {datetime.now().strftime('%H:%M:%S')}")

        channels = self.db.get_all_channels()
        if not channels:
            print("  ⚠ 没有频道可检查")
            return

        print(f"  共 {len(channels)} 个频道")

        # 分批检查（避免并发太多）
        batch_size = 50
        active_count = 0
        inactive_count = 0

        for i in range(0, len(channels), batch_size):
            batch = channels[i:i + batch_size]
            results = await run_health_check(batch)

            for ch in batch:
                result = results.get(ch.id)
                if result is None:
                    continue

                if result.is_active:
                    # 成功
                    new_fail = 0
                    new_success = ch.success_count + 1
                    active_count += 1
                else:
                    # 失败
                    new_fail = ch.fail_count + 1
                    new_success = 0
                    inactive_count += 1

                # 连续 MAX_FAIL_COUNT 次失败 → 标记 inactive
                is_active = new_fail < 3
                self.db.update_channel_status(
                    ch.id,
                    is_active=is_active,
                    fail_count=new_fail,
                    success_count=new_success,
                    response_time_ms=result.response_time_ms,
                )

            print(f"    批次 {i//batch_size + 1}: {len(batch)} 个")

        # 重新生成 M3U（排除失效源）
        self._generate_m3u()

        print(f"  ✅ 健康检查完成: {active_count} 活跃 / {inactive_count} 失效")
        return active_count, inactive_count

    # ─── 自动修复 ──────────────────────────────────────────────────

    async def run_deep_check(self):
        """深度检查：用 30s 超时重新测试所有失效频道"""
        print(f"  [DEEP] 深度检查失效频道... {datetime.now().strftime('%H:%M:%S')}")
        from checker import run_deep_check as _deep_check
        inactive = self.db.get_inactive_channels()
        if not inactive:
            print("  ✅ 没有需要深度检查的频道")
            return 0

        print(f"  共 {len(inactive)} 个失效频道，使用 30s 超时...")
        results = await _deep_check(inactive)
        recovered = 0
        for ch in inactive:
            result = results.get(ch.id)
            if result and result.is_active:
                # 频道恢复了！重新激活
                self.db.update_channel_status(ch.id, is_active=True, fail_count=0, success_count=1)
                print(f"    ✅ {ch.name} 已恢复! ({result.response_time_ms}ms)")
                recovered += 1

        if recovered > 0:
            self._generate_m3u()
            print(f"  ✅ 深度检查完成: {recovered}/{len(inactive)} 个已恢复")
        else:
            print(f"  ⚠ 深度检查完成: 0/{len(inactive)} 个恢复")
        return recovered

    async def run_auto_heal(self):
        """
        自动修复失效频道
        对 inactive 的频道，尝试重新搜刮并替换 URL
        """
        print(f"\n  🔧 开始自动修复... {datetime.now().strftime('%H:%M:%S')}")

        inactive = self.db.get_inactive_channels()
        if not inactive:
            print("  ✅ 没有需要修复的频道")
            return 0

        print(f"  发现 {len(inactive)} 个失效频道")

        self._init_scrapers()
        fixed_count = 0

        for ch in inactive:
            print(f"    🔍 修复: {ch.name} (原: {ch.url[:50]}...)")

            # 用搜刮器寻找同名的频道
            new_url = await self._find_replacement(ch)

            if new_url:
                self.db.update_channel_url(ch.id, new_url)
                print(f"      ✅ 已替换为: {new_url[:60]}...")
                fixed_count += 1

                record = ScrapeRecord(
                    channel_name=ch.name,
                    source_website="auto-heal",
                    url_found=new_url,
                    success=True,
                )
                self.db.add_scrape_record(record)
            else:
                print(f"      ❌ 未找到替代源")

        if fixed_count > 0:
            self._generate_m3u()
            print(f"  ✅ 修复完成: {fixed_count}/{len(inactive)} 个已修复")
        else:
            print(f"  ⚠ 未找到任何替代源")

        return fixed_count

    async def _find_replacement(self, channel: Channel) -> Optional[str]:
        """
        为失效频道寻找替代源
        从其他活跃频道中找同名不同源的，或重新搜索
        """
        # 1. 先看数据库中是否有同名的其它活跃频道
        same_name = self.db.get_channel_by_name(channel.name)
        for other in same_name:
            if other.id != channel.id and other.is_active and other.url != channel.url:
                print(f"      → 使用已有备用源")
                return other.url

        # 2. 重新搜刮该频道名
        for scraper in self.scrapers:
            try:
                all_channels = scraper.scrape()
                for ch_data in all_channels:
                    if ch_data["name"] == channel.name or \
                       channel.name in ch_data["name"] or \
                       ch_data["name"] in channel.name:
                        url = ch_data["url"]
                        if url and url != channel.url:
                            print(f"      → 从 {type(scraper).__name__} 找到新源")
                            return url
            except Exception as e:
                print(f"      → {type(scraper).__name__} 搜索失败: {e}")
                continue

        return None

    # ─── M3U 生成 ────────────────────────────────────────────────────

    def _generate_m3u(self):
        """生成 M3U 播放列表"""
        channels = self.db.get_active_channels()
        if not channels:
            print("  ⚠ 没有活跃频道，跳过 M3U 生成")
            return

        self.m3u.generate(channels)
        # 生成按协议分组的播放列表
        proto_content = self.m3u.generate_grouped_by_protocol(channels)
        proto_path = self.m3u.get_output_path().parent / "playlist_by_protocol.m3u"
        proto_path.write_text(proto_content, encoding="utf-8")
        print(f"  📺 M3U 已生成: {len(channels)} 个频道 (标准+按协议分组)")

    # ─── 辅助方法 ──────────────────────────────────────────────────

    def _dicts_to_channels(self, data: List[dict], scraper) -> List[Channel]:
        """字典列表转 Channel 对象"""
        channels = []
        for item in data:
            ch = Channel(
                name=item.get("name", ""),
                url=item.get("url", ""),
                group=item.get("group", "未分类"),
                region=item.get("region", self._auto_region(item)),
                logo=item.get("logo", ""),
                tvg_id=item.get("tvg_id", ""),
                source=item.get("source", f"scraper:{type(scraper).__name__}"),
                is_active=True,
            )
            if ch.name and ch.url:
                channels.append(ch)
        return channels

    def _auto_region(self, item: dict) -> str:
        """自动判断区域"""
        name = item.get("name", "")
        group = item.get("group", "")
        return self._classify_region(name + group)

    def _classify_region(self, text: str) -> str:
        text_lower = text.lower()
        for keyword, region in GROUP_REGION_MAP.items():
            if keyword.lower() in text_lower:
                return region
        return "mainland"

    def _count_new_channels(self, channels: List[Channel]) -> int:
        """统计新增频道数（简化版）"""
        existing = set()
        for ch in self.db.get_all_channels():
            existing.add((ch.name, ch.url))
        new = sum(1 for ch in channels if (ch.name, ch.url) not in existing)
        return new

    def _fix_grouping(self):
        """修正频道分组"""
        channels = self.db.get_all_channels()
        for ch in channels:
            region = self._classify_region(ch.name + ch.group)
            if region != ch.region:
                self.db.update_channel_group(ch.id, ch.group, region)


async def run_scheduled_tasks(scheduler: IPTVScheduler):
    """定时任务循环"""
    print("\n  ⏰ 定时任务已启动:")
    print(f"    健康检查: 每 {HEALTH_CHECK_INTERVAL_MINUTES} 分钟")
    print(f"    全量搜刮: 每 {SCRAPE_INTERVAL_HOURS} 小时")
    print(f"    自动修复: 每 {AUTO_HEAL_INTERVAL_MINUTES} 分钟")

    # 立即执行一次
    await scheduler.run_scrape()
    await scheduler.run_health_check()

    # schedule 库的定时
    schedule.every(HEALTH_CHECK_INTERVAL_MINUTES).minutes.do(
        lambda: asyncio.create_task(scheduler.run_health_check())
    )
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(
        lambda: asyncio.create_task(scheduler.run_scrape())
    )
    schedule.every(AUTO_HEAL_INTERVAL_MINUTES).minutes.do(
        lambda: asyncio.create_task(scheduler.run_auto_heal())
    )

    while True:
        schedule.run_pending()
        await asyncio.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="IPTV 直播源自动搜刮系统")
    parser.add_argument("--scrape", action="store_true", help="仅执行一次搜刮")
    parser.add_argument("--check", action="store_true", help="仅执行一次健康检查")
    parser.add_argument("--deep-check", action="store_true", help="深度检查失效频道（30s超时）")
    parser.add_argument("--server", action="store_true", help="仅启动 HTTP 服务")
    parser.add_argument("--full", action="store_true", help="完整启动（搜刮+检查+服务+调度）")
    parser.add_argument("--log-file", type=str, help="日志文件路径 (可选)")
    parser.add_argument("--menu", action="store_true", help="交互式管理菜单")

    args = parser.parse_args()

    # 如果指定了日志文件
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logging.getLogger().addHandler(file_handler)
        print(f"  [LOG] 日志文件: {args.log_file}")

    # 默认行为：完整启动
    if not any(vars(args).values()):
        args.full = True

    scheduler = IPTVScheduler()

    if args.menu:
        run_menu()
        return

    if args.scrape:
        asyncio.run(scheduler.run_scrape())

    elif args.check:
        asyncio.run(scheduler.run_health_check())

    elif args.server:
        # 如果已有数据，直接启动服务
        server = M3UServer(scheduler.db, scheduler.m3u, scheduler)
        server.start()

    elif args.full:
        server = M3UServer(scheduler.db, scheduler.m3u, scheduler)

        # 在单独的线程中运行定时任务
        import threading

        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_scheduled_tasks(scheduler))

        task_thread = threading.Thread(target=run_async_loop, daemon=True)
        task_thread.start()

        # 主线程启动 HTTP 服务
        try:
            server.start()
        except KeyboardInterrupt:
            print("\n  👋 正在停止...")
            sys.exit(0)


def run_menu():
    """启动交互式菜单"""
    from cli_menu import run_menu as _menu
    _menu()


if __name__ == "__main__":
    main()
