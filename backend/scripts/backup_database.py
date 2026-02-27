"""
Database Backup & Restore Utility

Automated PostgreSQL backup with compression, rotation, and restore support.
Can be run as a cron job or called from the application.

Usage:
    python -m scripts.backup_database backup
    python -m scripts.backup_database restore --file backups/backup_20240101_120000.sql.gz
    python -m scripts.backup_database list
    python -m scripts.backup_database cleanup --keep 7
"""

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def create_backup(output_dir: Path = BACKUP_DIR) -> Path:
    """
    Create a compressed PostgreSQL backup using pg_dump.

    Returns path to the backup file.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql.gz"
    output_path = output_dir / filename

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

    pg_dump_cmd = [
        "pg_dump",
        "-h", settings.POSTGRES_HOST,
        "-p", str(settings.POSTGRES_PORT),
        "-U", settings.POSTGRES_USER,
        "-d", settings.POSTGRES_DB,
        "--format=plain",
        "--no-owner",
        "--no-acl",
        "--verbose",
    ]

    logger.info("Starting backup: %s → %s", settings.POSTGRES_DB, output_path)

    try:
        result = subprocess.run(
            pg_dump_cmd,
            capture_output=True,
            env=env,
            timeout=600,  # 10 min timeout
        )

        if result.returncode != 0:
            logger.error("pg_dump failed: %s", result.stderr.decode())
            raise RuntimeError(f"pg_dump failed with code {result.returncode}")

        # Compress with gzip
        with gzip.open(output_path, "wb") as f:
            f.write(result.stdout)

        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info("Backup complete: %s (%.2f MB)", output_path.name, size_mb)
        return output_path

    except FileNotFoundError:
        logger.error("pg_dump not found. Ensure PostgreSQL client tools are installed.")
        raise
    except subprocess.TimeoutExpired:
        logger.error("Backup timed out after 600 seconds.")
        raise


def restore_backup(backup_path: str) -> None:
    """Restore a PostgreSQL backup from a compressed file."""
    path = Path(backup_path)
    if not path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

    logger.info("Restoring backup: %s → %s", path.name, settings.POSTGRES_DB)

    # Decompress
    if str(path).endswith(".gz"):
        with gzip.open(path, "rb") as f:
            sql_data = f.read()
    else:
        sql_data = path.read_bytes()

    psql_cmd = [
        "psql",
        "-h", settings.POSTGRES_HOST,
        "-p", str(settings.POSTGRES_PORT),
        "-U", settings.POSTGRES_USER,
        "-d", settings.POSTGRES_DB,
        "--single-transaction",
    ]

    result = subprocess.run(
        psql_cmd,
        input=sql_data,
        capture_output=True,
        env=env,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error("Restore failed: %s", result.stderr.decode())
        raise RuntimeError(f"psql restore failed with code {result.returncode}")

    logger.info("Restore complete from %s", path.name)


def list_backups(backup_dir: Path = BACKUP_DIR) -> list:
    """List all available backups sorted by date (newest first)."""
    backups = sorted(backup_dir.glob("backup_*.sql.gz"), reverse=True)

    for b in backups:
        size_mb = b.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(b.stat().st_mtime, tz=timezone.utc)
        print(f"  {b.name}  ({size_mb:.2f} MB)  {mtime.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    if not backups:
        print("  No backups found.")

    return backups


def cleanup_backups(keep: int = 7, backup_dir: Path = BACKUP_DIR) -> int:
    """Delete old backups, keeping the most recent `keep` files."""
    backups = sorted(backup_dir.glob("backup_*.sql.gz"), reverse=True)
    removed = 0

    for old_backup in backups[keep:]:
        old_backup.unlink()
        logger.info("Removed old backup: %s", old_backup.name)
        removed += 1

    logger.info("Cleanup: kept %d, removed %d backups", min(keep, len(backups)), removed)
    return removed


def main():
    parser = argparse.ArgumentParser(description="Database Backup Manager")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"])
    parser.add_argument("--file", help="Backup file path (for restore)")
    parser.add_argument("--keep", type=int, default=7, help="Number of backups to keep (for cleanup)")

    args = parser.parse_args()

    if args.action == "backup":
        create_backup()
    elif args.action == "restore":
        if not args.file:
            parser.error("--file is required for restore")
        restore_backup(args.file)
    elif args.action == "list":
        list_backups()
    elif args.action == "cleanup":
        cleanup_backups(keep=args.keep)


if __name__ == "__main__":
    main()
