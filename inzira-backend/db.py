from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import database_url


def _engine_options(url: str) -> dict:
    opts = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        opts["connect_args"] = {"check_same_thread": False}
    return opts


_db_url = database_url()
ENGINE = create_engine(_db_url, **_engine_options(_db_url))

SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
