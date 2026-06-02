"""
SQLite 数据库层
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List
from models import Channel, ScrapeRecord
from config import DB_PATH


class Database:
    def __init__(self, db_path: Union[str, Path] = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS channels (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            TEXT NOT NULL,
                    url             TEXT NOT NULL,
                    group_name      TEXT DEFAULT '',
                    region          TEXT DEFAULT 'mainland',
                    logo            TEXT DEFAULT '',
                    tvg_id          TEXT DEFAULT '',
                    source          TEXT DEFAULT '',
                    is_active       INTEGER DEFAULT 1,
                    fail_count      INTEGER DEFAULT 0,
                    success_count   INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    last_checked    TEXT,
                    kodi_props      TEXT DEFAULT '',
                    added_at        TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    UNIQUE(name, url)
                );

                CREATE TABLE IF NOT EXISTS scrape_records (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_name    TEXT NOT NULL,
                    source_website  TEXT NOT NULL,
                    url_found       TEXT DEFAULT '',
                    success         INTEGER DEFAULT 0,
                    checked_at      TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(name);
                CREATE INDEX IF NOT EXISTS idx_channels_region ON channels(region);
                CREATE INDEX IF NOT EXISTS idx_channels_active ON channels(is_active);
                CREATE INDEX IF NOT EXISTS idx_scrape_channel ON scrape_records(channel_name);
            """)
            # 数据库迁移：为旧数据库添加 kodi_props 列
            try:
                conn.execute("ALTER TABLE channels ADD COLUMN kodi_props TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # 列已存在

    # ─── Channel CRUD ────────────────────────────────────────────────

    def add_channel(self, channel: Channel) -> Optional[int]:
        """添加频道，已存在则更新"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            try:
                cursor = conn.execute(
                    """INSERT INTO channels (name, url, group_name, region, logo,
                        tvg_id, source, is_active, kodi_props, added_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name, url) DO UPDATE SET
                        updated_at = excluded.updated_at,
                        is_active = excluded.is_active,
                        source = excluded.source""",
                    (channel.name, channel.url, channel.group, channel.region,
                     channel.logo, channel.tvg_id, channel.source, 1, now, now)
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def add_channels_batch(self, channels: List[Channel]):
        """批量添加频道"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            for ch in channels:
                try:
                    conn.execute(
                        """INSERT INTO channels (name, url, group_name, region, logo,
                            tvg_id, source, is_active, kodi_props, added_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name, url) DO UPDATE SET
                            updated_at = excluded.updated_at,
                            is_active = excluded.is_active,
                            source = excluded.source""",
                        (ch.name, ch.url, ch.group, ch.region,
                         ch.logo, ch.tvg_id, ch.source, 1, ch.kodi_props, now, now)
                    )
                except sqlite3.IntegrityError:
                    continue

    def get_all_channels(self) -> List[Channel]:
        """获取所有频道"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM channels ORDER BY region, group_name, name"
            ).fetchall()
            return [self._row_to_channel(r) for r in rows]

    def get_active_channels(self) -> List[Channel]:
        """获取活跃频道"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM channels WHERE is_active=1 ORDER BY region, group_name, name"
            ).fetchall()
            return [self._row_to_channel(r) for r in rows]

    def get_inactive_channels(self) -> List[Channel]:
        """获取失效频道"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM channels WHERE is_active=0 ORDER BY fail_count DESC"
            ).fetchall()
            return [self._row_to_channel(r) for r in rows]

    def get_channel_by_name(self, name: str) -> List[Channel]:
        """按名称查找频道"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM channels WHERE name LIKE ? ORDER BY is_active DESC",
                (f"%{name}%",)
            ).fetchall()
            return [self._row_to_channel(r) for r in rows]

    def update_channel_status(self, channel_id: int, is_active: bool,
                               fail_count: int = 0, success_count: int = 0,
                               response_time_ms: int = 0):
        """更新频道状态"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE channels SET is_active=?, fail_count=?, success_count=?,
                    response_time_ms=?, last_checked=?, updated_at=?
                WHERE id=?""",
                (1 if is_active else 0, fail_count, success_count,
                 response_time_ms, now, now, channel_id)
            )

    def update_channel_url(self, channel_id: int, new_url: str):
        """更新频道 URL（自动修复用）"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE channels SET url=?, updated_at=?, is_active=1, fail_count=0 WHERE id=?",
                (new_url, now, channel_id)
            )

    def delete_channel(self, channel_id: int):
        """删除频道"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM channels WHERE id=?", (channel_id,))

    def count_channels(self) -> dict:
        """统计频道数量"""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM channels WHERE is_active=1").fetchone()[0]
            inactive = conn.execute("SELECT COUNT(*) FROM channels WHERE is_active=0").fetchone()[0]
            return {"total": total, "active": active, "inactive": inactive}

    def get_channels_by_region(self, region: str) -> List[Channel]:
        """按区域获取频道"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM channels WHERE region=? AND is_active=1 ORDER BY group_name, name",
                (region,)
            ).fetchall()
            return [self._row_to_channel(r) for r in rows]

    def update_channel_group(self, channel_id: int, group: str, region: str):
        """更正频道分组"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE channels SET group_name=?, region=?, updated_at=? WHERE id=?",
                (group, region, now, channel_id)
            )

    # ─── Scrape Records ─────────────────────────────────────────────

    def add_scrape_record(self, record: ScrapeRecord):
        """添加搜刮记录"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO scrape_records (channel_name, source_website, url_found, success, checked_at)
                VALUES (?, ?, ?, ?, ?)""",
                (record.channel_name, record.source_website, record.url_found,
                 1 if record.success else 0, record.checked_at)
            )

    def get_recent_scrapes(self, limit: int = 50) -> List[ScrapeRecord]:
        """最近搜刮记录"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM scrape_records ORDER BY checked_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [self._row_to_scrape(r) for r in rows]

    # ─── Helpers ─────────────────────────────────────────────────────

    def _row_to_channel(self, row: sqlite3.Row) -> Channel:
        return Channel(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            group=row["group_name"],
            region=row["region"],
            logo=row["logo"],
            tvg_id=row["tvg_id"],
            source=row["source"],
            is_active=bool(row["is_active"]),
            fail_count=row["fail_count"],
            success_count=row["success_count"],
            response_time_ms=row["response_time_ms"],
            last_checked=row["last_checked"],
            added_at=row["added_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_scrape(self, row: sqlite3.Row) -> ScrapeRecord:
        return ScrapeRecord(
            id=row["id"],
            channel_name=row["channel_name"],
            source_website=row["source_website"],
            url_found=row["url_found"],
            success=bool(row["success"]),
            checked_at=row["checked_at"],
        )
