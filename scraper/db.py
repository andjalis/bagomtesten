"""
db.py — SQLite state management for DR Kandidattest scraper.

Tracks all runs, prevents duplicate answer combinations,
and stores extracted candidate results.

Tables:
    runs            — One row per test run, tracks status and answer vector.
    results         — Candidate results (rank, name, party, match_pct) per run.
    candidate_media — Image URLs and profile links per candidate per run.
    questions       — Question texts extracted during scraping (idempotent).
"""

import aiosqlite
import json
import sqlite3
import time

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_hash TEXT NOT NULL,
    answers_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_msg TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    municipality TEXT NOT NULL DEFAULT 'Albertslund'
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    candidate_name TEXT NOT NULL,
    party TEXT NOT NULL,
    match_pct INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS candidate_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    candidate_name TEXT NOT NULL,
    candidate_url TEXT,
    candidate_image TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    category TEXT,
    UNIQUE(question_number, question_text)
);
"""

# Migration: remove UNIQUE constraint on answer_hash if it exists
# (same answers can be tested in different municipalities)
MIGRATIONS = [
    """CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_hash_mun
       ON runs(answer_hash, municipality);""",
]


async def init_db():
    """Initialize the database with schema and run migrations."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript(SCHEMA)

        # Drop the old UNIQUE constraint on answer_hash alone (if present)
        # SQLite doesn't support ALTER TABLE DROP INDEX, but we can check for it
        try:
            await conn.execute("DROP INDEX IF EXISTS sqlite_autoindex_runs_1")
        except Exception:
            pass

        for migration in MIGRATIONS:
            try:
                await conn.execute(migration)
            except Exception:
                pass  # Index may already exist
        await conn.commit()


async def cleanup_stale_runs():
    """Delete incomplete ('running') runs and their associated data.

    Called on startup to ensure that crashed/interrupted runs from a
    previous session don't leave orphaned data in the database or
    block re-attempts of those answer hashes.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Find stale run IDs
        cursor = await db.execute("SELECT id FROM runs WHERE status = 'running'")
        stale_ids = [row[0] for row in await cursor.fetchall()]

        if not stale_ids:
            return 0

        placeholders = ",".join("?" * len(stale_ids))
        await db.execute(f"DELETE FROM results WHERE run_id IN ({placeholders})", stale_ids)
        await db.execute(f"DELETE FROM candidate_media WHERE run_id IN ({placeholders})", stale_ids)
        await db.execute(f"DELETE FROM runs WHERE id IN ({placeholders})", stale_ids)
        await db.commit()
        return len(stale_ids)


async def is_duplicate(answer_hash: str, municipality: str = None) -> bool:
    """Check if an answer combination has already been completed successfully.

    Only considers runs with status='done'. Failed or running runs
    are NOT considered duplicates, allowing them to be retried.

    If municipality is provided, checks the (hash, municipality) pair.
    If not, checks if any done run with this hash exists.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        if municipality:
            cursor = await conn.execute(
                "SELECT 1 FROM runs WHERE answer_hash = ? AND municipality = ? AND status = 'done'",
                (answer_hash, municipality),
            )
        else:
            cursor = await conn.execute(
                "SELECT 1 FROM runs WHERE answer_hash = ? AND status = 'done'",
                (answer_hash,),
            )
        row = await cursor.fetchone()
        return row is not None


async def count_done_for_municipality(municipality: str) -> int:
    """Count how many completed runs exist for a given municipality."""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM runs WHERE municipality = ? AND status = 'done'",
            (municipality,),
        )
        row = await cursor.fetchone()
        return row[0]


async def register_run(answer_hash: str, answers: list[int], municipality: str = "Albertslund") -> int:
    """Register a new run. Returns run_id.

    If a previous run with the same (answer_hash, municipality) pair exists
    but is not 'done', it is deleted first (along with its partial results/media)
    to allow a clean retry.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        # Clean up any non-done previous attempt with this hash+municipality
        cursor = await conn.execute(
            "SELECT id FROM runs WHERE answer_hash = ? AND municipality = ? AND status != 'done'",
            (answer_hash, municipality),
        )
        old_rows = await cursor.fetchall()
        if old_rows:
            old_ids = [r[0] for r in old_rows]
            ph = ",".join("?" * len(old_ids))
            await conn.execute(f"DELETE FROM results WHERE run_id IN ({ph})", old_ids)
            await conn.execute(f"DELETE FROM candidate_media WHERE run_id IN ({ph})", old_ids)
            await conn.execute(f"DELETE FROM runs WHERE id IN ({ph})", old_ids)

        cursor = await conn.execute(
            """INSERT INTO runs (answer_hash, answers_json, status, started_at, municipality)
               VALUES (?, ?, 'running', ?, ?)""",
            (answer_hash, json.dumps(answers), time.time(), municipality),
        )
        await conn.commit()
        return cursor.lastrowid


async def mark_complete(run_id: int):
    """Mark a run as completed."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE runs SET status = 'done', completed_at = ? WHERE id = ?",
            (time.time(), run_id),
        )
        await db.commit()


async def mark_failed(run_id: int, error: str):
    """Mark a run as failed with error message."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE runs SET status = 'failed', error_msg = ?, completed_at = ? WHERE id = ?",
            (error, time.time(), run_id),
        )
        await db.commit()


async def save_results(run_id: int, candidates: list[dict]):
    """Save candidate results for a run.

    candidates: list of {rank, name, party, match_pct, url, image}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        for c in candidates:
            await db.execute(
                """INSERT INTO results (run_id, rank, candidate_name, party, match_pct)
                   VALUES (?, ?, ?, ?, ?)""",
                (run_id, c["rank"], c["name"], c["party"], c["match_pct"]),
            )
            await db.execute(
                """INSERT INTO candidate_media (run_id, candidate_name, candidate_url, candidate_image)
                   VALUES (?, ?, ?, ?)""",
                (run_id, c["name"], c.get("url", ""), c.get("image", ""))
            )
        await db.commit()


async def save_questions(questions: list[dict]):
    """Save question texts (idempotent via UNIQUE constraint).

    questions: list of {number, text, category}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        for q in questions:
            await db.execute(
                """INSERT OR IGNORE INTO questions (question_number, question_text, category)
                   VALUES (?, ?, ?)""",
                (q["number"], q["text"], q.get("category", "")),
            )
        await db.commit()


async def get_stats() -> dict:
    """Get overview statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        total = await (await db.execute("SELECT COUNT(*) FROM runs")).fetchone()
        done = await (await db.execute("SELECT COUNT(*) FROM runs WHERE status='done'")).fetchone()
        failed = await (await db.execute("SELECT COUNT(*) FROM runs WHERE status='failed'")).fetchone()
        running = await (await db.execute("SELECT COUNT(*) FROM runs WHERE status='running'")).fetchone()

        # Calculate speed: tests per hour over last hour
        one_hour_ago = time.time() - 3600
        recent = await (
            await db.execute(
                "SELECT COUNT(*) FROM runs WHERE status='done' AND completed_at > ?",
                (one_hour_ago,),
            )
        ).fetchone()

        return {
            "total": total[0],
            "done": done[0],
            "failed": failed[0],
            "running": running[0],
            "speed_per_hour": recent[0],
        }
