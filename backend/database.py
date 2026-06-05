"""Database setup with SQLAlchemy + optional sqlcipher3 encryption."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import DATABASE_URL, DATABASE_ENCRYPT_KEY


class Base(DeclarativeBase):
    pass


def _apply_encryption(dbapi_connection, connection_record):
    """Apply AES-256 encryption key after connecting."""
    if DATABASE_ENCRYPT_KEY:
        cursor = dbapi_connection.cursor()
        cursor.execute(f"PRAGMA key = '{DATABASE_ENCRYPT_KEY}'")
        cursor.close()


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

event.listen(engine, "connect", _apply_encryption)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup."""
    import backend.models.models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
