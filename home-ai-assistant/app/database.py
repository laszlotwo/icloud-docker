from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from alembic import command
    from alembic.config import Config
    import os
    import logging

    logger = logging.getLogger(__name__)

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

    # Create FTS5 virtual table for device manuals (best-effort; may not be available in all SQLite builds)
    fts_statements = [
        """CREATE VIRTUAL TABLE IF NOT EXISTS device_manuals_fts
           USING fts5(name, content, tags, content=device_manuals, content_rowid=id)""",
        """CREATE TRIGGER IF NOT EXISTS device_manuals_ai AFTER INSERT ON device_manuals BEGIN
               INSERT INTO device_manuals_fts(rowid, name, content, tags)
               VALUES (new.id, new.name, new.content, COALESCE(new.tags, ''));
           END""",
        """CREATE TRIGGER IF NOT EXISTS device_manuals_ad AFTER DELETE ON device_manuals BEGIN
               INSERT INTO device_manuals_fts(device_manuals_fts, rowid, name, content, tags)
               VALUES ('delete', old.id, old.name, old.content, COALESCE(old.tags, ''));
           END""",
        """CREATE TRIGGER IF NOT EXISTS device_manuals_au AFTER UPDATE ON device_manuals BEGIN
               INSERT INTO device_manuals_fts(device_manuals_fts, rowid, name, content, tags)
               VALUES ('delete', old.id, old.name, old.content, COALESCE(old.tags, ''));
               INSERT INTO device_manuals_fts(rowid, name, content, tags)
               VALUES (new.id, new.name, new.content, COALESCE(new.tags, ''));
           END""",
    ]
    try:
        with engine.connect() as conn:
            for stmt in fts_statements:
                conn.execute(text(stmt))
            conn.commit()
    except Exception as e:
        logger.warning("FTS5 setup skipped: %s", e)
