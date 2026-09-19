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

        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_scores (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                username TEXT,
                points INTEGER NOT NULL DEFAULT 0,
                correct_answers INTEGER NOT NULL DEFAULT 0,
                quizzes_answered INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
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
        return row[0] if row else default


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


async def add_ban(chat_id: int, admin_id: int, target_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO bans (chat_id, admin_id, target_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, admin_id, target_id, time.time())
        )
        await db.commit()


async def bans_last_24h(chat_id: int, admin_id: int) -> int:
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
            (chat_id, admin_id, cutoff)
        )
        row = await cursor.fetchone()
        return int(row[0] or 0)


async def add_quiz_result(
    chat_id: int,
    user_id: int,
    name: str,
    username: str | None,
    correct: bool
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO quiz_scores (
                chat_id, user_id, name, username,
                points, correct_answers, quizzes_answered
            )
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                name = excluded.name,
                username = excluded.username,
                points = quiz_scores.points + excluded.points,
                correct_answers =
                    quiz_scores.correct_answers + excluded.correct_answers,
                quizzes_answered =
                    quiz_scores.quizzes_answered + 1
            """,
            (
                chat_id,
                user_id,
                name,
                username,
                1 if correct else 0,
                1 if correct else 0,
            )
        )
        await db.commit()


async def get_leaderboard(chat_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT user_id, name, username, points,
                   correct_answers, quizzes_answered
            FROM quiz_scores
            WHERE chat_id = ?
            ORDER BY points DESC, correct_answers DESC, quizzes_answered ASC
            LIMIT ?
            """,
            (chat_id, limit)
        )
        return await cursor.fetchall()


async def get_user_stats(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT name, username, points,
                   correct_answers, quizzes_answered
            FROM quiz_scores
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        )
        return await cursor.fetchone()
