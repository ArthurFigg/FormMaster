from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import configuracoes

_kwargs = {"check_same_thread": False} if configuracoes.DATABASE_URL.startswith("sqlite") else {}
motor = create_engine(configuracoes.DATABASE_URL, connect_args=_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
