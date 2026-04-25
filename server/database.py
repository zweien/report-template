from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from server.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
    Base.metadata.create_all(bind=engine)
    # Add new columns to existing tables
    with engine.connect() as conn:
        insp = inspect(engine)
        cols = {c["name"] for c in insp.get_columns("drafts")}
        if "section_enabled" not in cols:
            conn.execute(text(
                "ALTER TABLE drafts ADD COLUMN section_enabled JSON DEFAULT '{}'"
            ))
            conn.commit()
