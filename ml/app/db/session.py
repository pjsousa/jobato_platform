from __future__ import annotations

from pathlib import Path
from threading import Lock

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


_MIGRATION_LOCK = Lock()
_MIGRATED_DATABASES: set[Path] = set()


def build_engine(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    return engine


def open_session(db_path: Path) -> Session:
    _ensure_migrations(db_path)
    engine = build_engine(db_path)
    return Session(engine)


def _ensure_migrations(db_path: Path) -> None:
    normalized_path = db_path.resolve()
    if normalized_path in _MIGRATED_DATABASES:
        return

    with _MIGRATION_LOCK:
        if normalized_path in _MIGRATED_DATABASES:
            return
        _run_migrations(normalized_path)
        _MIGRATED_DATABASES.add(normalized_path)


def _run_migrations(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    config = Config(str(_alembic_ini_path()))
    config.set_main_option("script_location", str(_migrations_path()))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")


def _alembic_ini_path() -> Path:
    return Path(__file__).resolve().parent / "alembic.ini"


def _migrations_path() -> Path:
    return Path(__file__).resolve().parent / "migrations"
