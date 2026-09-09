"""Lightweight, zero-dependency SQL migration runner for GAIA OS."""

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations(db: aiosqlite.Connection) -> list[str]:
    """Runs all unapplied SQL migrations within a transaction.

    Args:
        db: Open aiosqlite Connection.

    Returns:
        List of applied migration version filenames.
    """
    # Ensure schema_migrations table exists
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    await db.commit()

    # Query already applied migrations
    async with db.execute("SELECT version FROM schema_migrations") as cursor:
        rows = await cursor.fetchall()
        applied = {row[0] for row in rows}

    applied_now: list[str] = []

    # Read and sort migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for file_path in migration_files:
        version = file_path.name
        if version in applied:
            continue

        sql_content = file_path.read_text(encoding="utf-8")

        # Execute migration script
        await db.executescript(sql_content)

        # Record migration
        applied_at = datetime.now(UTC).isoformat()
        await db.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (version, applied_at),
        )
        await db.commit()
        applied_now.append(version)

    return applied_now
