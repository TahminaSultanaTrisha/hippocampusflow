"""Alembic environment. Migrations are version control for your database:
every schema change is a numbered script, so any laptop or server can be
brought to the exact same schema with `alembic upgrade head`."""
import sys
from logging.config import fileConfig
from pathlib import Path

# Alembic runs as a standalone tool, so it doesn't automatically know where
# our `app` package lives. Add the backend root (parent of this folder).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.session import Base

# Import every model module here so autogenerate can see the tables.
from app.models import action, memory, message, scan, scan_result, user  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
