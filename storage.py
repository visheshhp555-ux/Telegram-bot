import time
from pathlib import Path

import aiosqlite


DB_PATH = Path("bot.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
        """)

        await db.commit()


async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )

        row = await cursor.fetchone()

        if row:
            return row[0]

        return default


async def set_setting(key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """,
            (key, str(value))
        )

        await db.commit()


async def add_ban(
    chat_id: int,
    admin_id: int,
    target_id: int
):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            """
            INSERT INTO bans (
                chat_id,
                admin_id,
                target_id,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                admin_id,
                target_id,
                time.time()
            )
        )

        await db.commit()


async def bans_last_24h(
    chat_id: int,
    admin_id: int
) -> int:

    cutoff = time.time() - (24 * 60 * 60)

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM bans
            WHERE chat_id = ?
            AND admin_id = ?
            AND created_at > ?
            """,
            (
                chat_id,
                admin_id,
                cutoff
            )
        )

        row = await cursor.fetchone()

        return int(row[0] or 0)
