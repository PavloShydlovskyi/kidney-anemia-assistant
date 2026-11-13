"""Спільне для тестів.

Застосунок за замовчуванням (main.create_app()) працює з SQLite. Щоб тести не
чіпали робочу kidney.db, тут для всього прогону задається тимчасова БД,
створена міграціями Alembic — тобто так само, як у роботі.
"""
import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND = Path(__file__).resolve().parents[1]

_tmp_dir = tempfile.TemporaryDirectory(prefix="kidney-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp_dir.name) / 'app.db'}"


def alembic_config() -> Config:
    """Конфігурація без alembic.ini, щоб тести не перебудовували логування."""
    config = Config()
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    return config


command.upgrade(alembic_config(), "head")
