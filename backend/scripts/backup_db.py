"""Резервна копія SQLite і перевірка її цілісності.

Запуск з папки backend:
    python scripts/backup_db.py kidney.db backups/kidney-2026-11-13.db

Відповідальний: Database Developer.
"""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def backup_database(source: Path, target: Path) -> None:
    """Копіює БД через sqlite3 backup API (безпечно під час роботи сервера)."""
    if not source.exists():
        raise FileNotFoundError(f"Базу даних {source} не знайдено")
    target.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source)) as source_db, \
            closing(sqlite3.connect(target)) as target_db:
        source_db.backup(target_db)


def check_integrity(path: Path) -> bool:
    """PRAGMA integrity_check повертає 'ok'."""
    with closing(sqlite3.connect(path)) as db:
        return db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Резервна копія бази даних")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args(argv)

    backup_database(args.source, args.target)
    if not check_integrity(args.target):
        print("Копія пошкоджена")
        return 1
    print(f"Копію збережено: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
