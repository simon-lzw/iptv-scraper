"""
交互式 CLI 管理菜单

用法: python main.py --menu

功能:
  - 查看系统状态
  - 手动触发搜刮
  - 查看频道列表（按区域）
  - 查看失效频道
  - 手动触发修复
"""
import asyncio
import sys
from db import Database
from m3u_generator import M3UGenerator
from main import IPTVScheduler


class CLIMenu:
    """终端交互菜单"""

    def __init__(self):
        self.scheduler = IPTVScheduler()
        self.db = self.scheduler.db

    def run(self):
        """启动菜单"""
        while True:
            self._show_header()
            self._show_menu()
            choice = input("\n  请输入选项 [1-7]: ").strip()

            if choice == "1":
                self._show_status()
            elif choice == "2":
                asyncio.run(self.scheduler.run_scrape())
            elif choice == "3":
                self._show_channels()
            elif choice == "4":
                self._show_inactive()
            elif choice == "5":
                asyncio.run(self.scheduler.run_auto_heal())
            elif choice == "6":
                asyncio.run(self.scheduler.run_health_check())
            elif choice == "d":
                asyncio.run(self.scheduler.run_deep_check())
            elif choice == "7":
                print("\n  👋 再见！")
                break
            else:
                print("\n  ⚠ 无效选项，请重新输入")

            input("\n  按 Enter 继续...")

    def _show_header(self):
        """显示标题"""
        print("\n" + "=" * 50)
        print("  📺 IPTV 直播源管理系统")
        print("=" * 50)

    def _show_menu(self):
        """显示菜单"""
        stats = self.db.count_channels()
        print(f"\n  📊 当前状态: {stats['total']} 频道 | {stats['active']} 活跃 | {stats['inactive']} 失效")
        print()
        print("  ┌─────────────────────────────────────┐")
        print("  │ 1. 📊 查看详细状态                   │")
        print("  │ 2. 🔍 执行搜刮                       │")
        print("  │ 3. 📺 查看频道列表                   │")
        print("  │ 4. ❌ 查看失效频道                   │")
        print("  │ 5. 🔧 修复失效频道                   │")
        print("  │ 6. 🏥 健康检查                       │")
        print("  │ 7. 🚪 退出                           │")
        print("  └─────────────────────────────────────┘")

    def _show_status(self):
        """显示详细状态"""
        stats = self.db.count_channels()
        print(f"\n  📊 系统状态")
        print(f"  {'='*40}")
        print(f"  总频道:   {stats['total']}")
        print(f"  活跃:     {stats['active']} ({stats['active']/max(stats['total'],1)*100:.0f}%)")
        print(f"  失效:     {stats['inactive']}")
        print()

        # 按区域统计
        for region, label in [("mainland", "中国大陆"), ("hongkong", "香港"), ("macau", "澳门"), ("taiwan", "台湾")]:
            channels = self.db.get_channels_by_region(region)
            print(f"  {label}: {len(channels)} 频道")

        # 搜刮源统计
        from collections import Counter
        sources = Counter(ch.source for ch in self.db.get_all_channels())
        print(f"\n  搜刮源分布:")
        for src, cnt in sources.most_common():
            print(f"    {src}: {cnt}")

    def _show_channels(self):
        """显示频道列表（按区域筛选）"""
        print("\n  选择区域:")
        print("    1. 中国大陆")
        print("    2. 香港")
        print("    3. 澳门")
        print("    4. 台湾")
        print("    5. 全部")

        choice = input("\n  请输入 [1-5]: ").strip()
        region_map = {"1": "mainland", "2": "hongkong", "3": "macau", "4": "taiwan", "5": None}

        region = region_map.get(choice)
        if region is None:
            channels = self.db.get_all_channels()
        elif region:
            channels = self.db.get_channels_by_region(region)
        else:
            return

        if not channels:
            print("  ⚠ 没有频道")
            return

        print(f"\n  📺 共 {len(channels)} 个频道:")
        print(f"  {'='*60}")
        seen = set()
        for ch in channels:
            name_clean = ch.name.split(" (")[0].split(" [")[0]
            if name_clean not in seen:
                seen.add(name_clean)
                status = "✓" if ch.is_active else f"✗(×{ch.fail_count})"
                print(f"  [{status}] {name_clean}")
        print(f"\n  (去重后 {len(seen)} 个唯一频道)")

    def _show_inactive(self):
        """显示失效频道"""
        channels = self.db.get_inactive_channels()
        if not channels:
            print("\n  ✅ 没有失效频道")
            return

        print(f"\n  ❌ 失效频道 ({len(channels)}):")
        for ch in channels:
            print(f"  - {ch.name} (失败 {ch.fail_count} 次)")


def run_menu():
    """入口函数"""
    menu = CLIMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print("\n\n  👋 再见！")
        sys.exit(0)


if __name__ == "__main__":
    run_menu()
