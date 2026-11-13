"""Резервна копія SQLite і перевірка її цілісності.

Запуск з папки backend:
    python scripts/backup_db.py kidney.db backups/kidney-2026-11-13.db

Відповідальний: Database Developer.
"""
import argparse
from pathlib import Path


def backup_database(source: Path, target: Path) -> None:
    """Копіює БД через sqlite3 backup API (безпечно під час роботи сервера).

    TODO: sqlite3.connect(source).backup(sqlite3.connect(target)).
    """
    raise NotImplementedError


def check_integrity(path: Path) -> bool:
    """TODO: PRAGMA integrity_check повертає 'ok'."""
    raise NotImplementedError


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
